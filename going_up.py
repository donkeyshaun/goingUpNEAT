import pygame as pg
import random
import os
import math
import neat
vec = pg.math.Vector2



pg.init()
pg.display.set_caption("Going up?")
win_obj = pg.display.Info()
scr_size = 800

WIN = pg.display.set_mode((scr_size, win_obj.current_h))


DRAW_LINES = False
quit_game = False

#PRINT INFO VARS  
vel = 10
gen = 0
max_Score = 0
max_Gen = 0
max_Genome = 0


bg_y = -22500+win_obj.current_h
pl_art = [pg.image.load("sprites/platform.png").convert(),pg.image.load("sprites/platform_red.png").convert(),pg.image.load("sprites/platform_blue.png").convert()]
bg_art = pg.transform.scale(pg.image.load("sprites/bg.png").convert(),(scr_size, 22500))
death_sound = pg.mixer.Sound("audio/death.wav")
STAT_FONT = pg.font.SysFont("comicsans", 50)



class Platform:
    platform_art = pl_art
    win_h = win_obj.current_h
    win_w = scr_size
    def __init__(self, color):
        self.y_offset = 300
        self.w = 100
        self.h = 25
        self.pos = vec(random.randrange(0,self.win_w-self.w),random.randrange(-self.y_offset,self.win_h))
        self.color = color
        if self.color == "Red":
            self.y_offset = self.y_offset*5
            self.img = pg.transform.scale(self.platform_art[1],(self.w, self.h))
        elif self.color == "Blue":
            self.y_offset = self.y_offset*7
            self.img = pg.transform.scale(self.platform_art[2],(self.w, self.h))
            if self.pos.x > self.win_w/2:
                self.hor_vel = 5
            else:
                self.hor_vel = -5
        else:
            self.img = pg.transform.scale(self.platform_art[0],(self.w, self.h))
        self.rect = self.img.get_rect(center=(self.pos.x, self.pos.y))

    def moveDown(self, win, pl_y):
        if self.pos.y >= self.win_h:
            if min(pl_y)-self.y_offset < 0:
                self.pos.y = min(pl_y)-self.y_offset
            else:
                self.pos.y = random.randrange(-self.y_offset, 0)
            self.pos.x = random.randrange(0,scr_size-self.w)

        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        win.blit(self.img, (self.pos.x, self.pos.y))
    
    def moveLF(self, win):
        if self.pos.x+self.w >= scr_size:
            self.hor_vel = -self.hor_vel

        elif self.pos.x <= 0:
            self.hor_vel = -self.hor_vel
        self.pos.x += self.hor_vel
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        win.blit(self.img, (self.pos.x, self.pos.y))

    
        
class Blob:

    win_h = win_obj.current_h
    win_w = scr_size
    def __init__(self, x, y):
        self.pos = vec(x, y)
        self.size = 50
        self.jump = False
        self.gravity = 0
        self.img = pg.transform.scale(pg.image.load("sprites/blob_1.png").convert_alpha(), (self.size, self.size))
        self.jump_force = 0
        self.max_jump_force = 20 
        self.init_game = False
        self.rect = self.img.get_rect(center=(self.pos.x-self.size/2, self.pos.y-self.size))
        self.horizontal_vel = 0
        self.max_hor_vel = 20
        self.last_dir = 0

    
    def update_pos(self, win, pl_x, pl_y):
        if self.jump:
            if self.pos.y - self.jump_force > 0:
                self.pos.y -= self.jump_force
            self.jump_force -= 1
        if self.jump_force <= 0:
            self.jump = False  
            self.pos.y -= self.jump_force
            self.jump_force -= 1
        if self.pos.y - self.jump_force >= self.win_h - self.size and self.init_game:
            self.jump = True
            self.jump_force = self.max_jump_force


        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        win.blit(self.img, (self.pos.x, self.pos.y))

    def collide(self, platforms):
        hit = pg.sprite.spritecollide(self, platforms, False)

        if hit and self.jump_force <= 0:
            for pl in hit:
                if pl.color == "Red":
                    platforms.remove(pl)
            self.init_game = False
            self.jump = True
            self.jump_force = self.max_jump_force
            return True

        return False

    def lookInDir(self, dir, platforms):
        temp = self.rect
        distance = []
        if dir == "RIGHT":
            self.rect = pg.Rect(self.pos.x, self.pos.y, self.win_w, self.size)
        elif dir == "LEFT":
            self.rect = pg.Rect(self.pos.x-self.win_w, self.pos.y, self.win_w, self.size)
        elif dir == "DOWN":
            self.rect = pg.Rect(self.pos.x, self.pos.y, self.size, self.win_w)
        elif dir == "UP":
            self.rect = pg.Rect(self.pos.x, self.pos.y-self.win_w, self.size, self.win_w)
        hit = pg.sprite.spritecollide(self, platforms, False)
        self.rect = temp

        if hit:
            for platform in hit:
                if dir == "RIGHT" or dir == "LEFT": 
                    distance.append(abs(platform.pos.x + platform.w - self.pos.x + self.size/2))
                elif dir == "UP" or dir == "DOWN":
                    distance.append(abs(platform.pos.y + platform.h - self.pos.y - self.size/2))
            return min(distance)

        return 0

    def move_horizontal(self, direction):
        if direction != self.last_dir or direction == 0:
            self.horizontal_vel = 0
        if direction == -1:
            if self.pos.x - self.horizontal_vel <= 0:
                self.pos.x = 0
            else:
                self.pos.x -= self.horizontal_vel
        if direction == 1:
            if self.pos.x + self.horizontal_vel >= scr_size-self.size:
                self.pos.x = scr_size-self.size
            else:
                self.pos.x += self.horizontal_vel
        if self.horizontal_vel < self.max_hor_vel:
            self.horizontal_vel += 1

        self.last_dir = direction

def drawNet(win, genome):
    y_graph = 0
    x_graph = 700
    input_nodes = 8
    output_nodes = 3
    circle_radius = 10
    y_offset = (circle_radius*2+circle_radius)
    x_offset = y_offset*2
    max_offset = y_offset*max([input_nodes,output_nodes])
    offset_pos = 0

    if genome != 0:
        #Draw circles
        node_layers = []
        layer = []
        for node in range(input_nodes):
            layer.append(-node-1)
        node_layers.append(layer)
        layer = []
        for node in genome.nodes:
            if node not in range(output_nodes):
                if len(layer) >= 4:
                    node_layers.append(layer)
                    layer = []
                layer.append(node)
        if len(layer) > 0:
            node_layers.append(layer)
        layer = []
        for node in range(output_nodes):
            layer.append(node)
        node_layers.append(layer)

        if len(node_layers) > 2:
            x_graph -= (len(node_layers)-2)*x_offset


        for layer_id in range(len(node_layers)):
            for node_id in range(len(node_layers[layer_id])):
                if node_id % 2 > 0:
                    offset_pos += 1
                pg.draw.circle(win,(255,0,0),(round(x_graph+x_offset*layer_id),round(y_graph+max_offset/2 + y_offset*offset_pos)),circle_radius)
                offset_pos = -offset_pos
            offset_pos = 0


        #Draw Connections
        for con in genome.connections:
            node_one_y = 0
            node_one_x = 0
            node_two_y = 0
            node_two_x = 0
            for layer_id in range(len(node_layers)):
                for node_id in range(len(node_layers[layer_id])):
                    temp = node_layers[layer_id]
                    if node_id % 2 > 0:
                        offset_pos += 1
                    if con[0] == temp[node_id]:
                        node_one_y = offset_pos
                        node_one_x = layer_id
                    if con[1] == temp[node_id]:
                        node_two_y = offset_pos
                        node_two_x = layer_id
                    offset_pos = -offset_pos
                offset_pos = 0
            pg.draw.line(win,(0,0,0), (round(x_graph+x_offset*node_one_x),round(y_graph+max_offset/2 + y_offset*node_one_y)),(round(x_graph+x_offset*node_two_x),round(y_graph+max_offset/2 + y_offset*node_two_y)), 2)



def update_win(win, platforms, pl_x, pl_y, blobs, speed, score, gen, pl_pos, highest_y, current_Genome):
    global bg_y, max_y, max_Score
    win.blit(bg_art, (0, bg_y))
    for platform in platforms:
        platform.moveDown(win, pl_y)
        if platform.color == "Blue":
            platform.moveLF(win)
        pl_pos[platforms.index(platform)] = platforms[platforms.index(platform)].pos
        pl_x[platforms.index(platform)]= platforms[platforms.index(platform)].pos.x
        pl_x[platforms.index(platform)]= platforms[platforms.index(platform)].pos.y

    for blob in blobs:
        if blob.pos.y < highest_y and blob.jump:
            highest_y = blob.pos.y
            score += 1
            
            for platform in platforms:
                platform.pos.y += blob.jump_force*3
                bg_y += blob.jump_force/20
                if bg_y >= 0:
                    bg_y = -22500/3 
                pl_pos[platforms.index(platform)] = platforms[platforms.index(platform)].pos
                pl_x[platforms.index(platform)]= platforms[platforms.index(platform)].pos.x
                pl_x[platforms.index(platform)]= platforms[platforms.index(platform)].pos.y

      
        blob.update_pos(win, pl_x, pl_y)
    
    #Draw Network of the current genome 
    drawNet(win, current_Genome)

    
    # score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 0, 0))
    win.blit(score_label, (10, 50))

    # generations
    score_label = STAT_FONT.render("Gene: " + str(gen), 1, (255, 0, 0))
    win.blit(score_label, (10, 90))

    # Highscore
    score_label = STAT_FONT.render("Highscore: " + str(max_Score), 1, (255, 0, 0))
    win.blit(score_label, (10, 10))


    pg.display.update()
    return score



def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # Run for up to x generations.
    winner = p.run(run_game, 400)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


def run_game(genomes, config):
    global WIN, gen, bg_y, max_Score, max_Gen, max_Genome, current_Genome
    quit_game = False
    win = WIN
    speed = 5
    num_platforms = 14
    clock = pg.time.Clock()
    for genome_id, genome in genomes:
        platforms = []
        platforms.append(Platform("Red"))
        platforms.append(Platform("Blue"))
        for i in range(num_platforms-len(platforms)):
            platforms.append(Platform(""))

        score = 0
        pl_x = [0]*len(platforms)
        pl_y = [0]*len(platforms)
        pl_pos = [0]*len(platforms)
        highest_y = win_obj.current_h
        blobs = []
        deaths = 0
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        blobs.append(Blob(450/2, 0))

        while blobs != [] and not quit_game:
            clock.tick(30)
        
            score = update_win(win, platforms, pl_x, pl_y, blobs, speed, score, gen, pl_pos, highest_y, genome)

            # COLLISION

            for blob in blobs:

                r_dist = blob.lookInDir("RIGHT",platforms)
                l_dist = blob.lookInDir("LEFT",platforms)
                u_dist = blob.lookInDir("UP",platforms)
                d_dist = blob.lookInDir("DOWN",platforms)
                dr_dist = 0
                dl_dist = 0
                ur_dist = 0
                ul_dist = 0

                if blob.collide(platforms):
                    genome.fitness += 10
                    if len(platforms) != num_platforms:
                        pl = Platform("Red")
                        pl.pos.y = -pl.y_offset
                        platforms.append(pl)

                #Distance to closest Platform
                min_dist = win_obj.current_h

                for pos in pl_pos:
                    distance = math.sqrt((pos.x - blob.pos.x + blob.size/2)**2+(pos.y-blob.pos.y)**2)
                    if distance <= min_dist and pos.y > blob.pos.y:
                        min_dist = distance
                        if blob.pos.x > pos.x:
                            if pos.y > blob.pos.y:
                                ul_dist = min_dist
                            else:
                                dl_dist = min_dist
                        else:
                            dl_dist = 0
                            ul_dist = 0

                        if blob.pos.x < pos.x:
                            if pos.y > blob.pos.y:
                                ur_dist = min_dist
                            else:
                                dr_dist = min_dist
                        else:
                            dr_dist = 0
                            ur_dist = 0
                       


                
                output = net.activate([r_dist, l_dist, u_dist, d_dist, dr_dist, dl_dist, ur_dist, ul_dist])
                maxOut = max(output)
                if output[0] == maxOut and output[0] > 0.5 :
                    blob.move_horizontal(-1)
                elif output[1] == maxOut and output[1] > 0.5:
                    blob.move_horizontal(1)
                else:
                    blob.move_horizontal(0)

                #Deaths if below screen
                deaths = len(blobs)

                if blob.pos.y > win_obj.current_h:
                    blobs.remove(blob)
                else:
                    genome.fitness = score
            
            if len(blobs) < deaths:
                death_sound.play()



            for event in pg.event.get():
                if event.type == pg.QUIT:
                    quit_game = True
                    pg.quit()
        if max_Score < score:
            max_Score = score
            max_Gen = gen
            max_Genome = genome_id
        bg_y = -22500+win_obj.current_h
    print("MAX SCORE IN ALL GENS: ")
    print(max_Score)
    print("IN GEN: ")
    print(max_Gen)
    print("WITH GENOME:")
    print(max_Genome)
    gen += 1



if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
