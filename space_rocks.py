# Space Rocks game.

import cartesian_coordinates as cc      # Functions for rotating, scaling, etc.
import pygame                           # 2d games engine.
import random
import time
import datetime                         # Needed for logging.


# If debugging is turned on, send the parm message to stdout.
def trace(config, message):
    if config.debug:
        print(datetime.datetime.now(), message)


############################################
# The rocks that float in space.
############################################

class Rock:

    def __init__(self, config, size):
        assert size in ['Small', 'Medium', 'Large']

        self.size = size                                    # Size of rock to be created, "Large", "Medium", "Small"
        self.vertices = []                                  # List of vertices of the rock, centered around origin.

        # Rock is based on a polygon (straight edged circle).
        if self.size == 'Large':
            self.radius = random.randint(30, 50)
        elif self.size == "Medium":
            self.radius = random.randint(15, 25)
        else:
            self.radius = random.randint(10, 15)

        self.rotation = 0                                   # Current rotation of the rock in degrees.

        max_rotation_velocity = round(100 / config.target_fps)
        self.rotation_speed = random.randint(- max_rotation_velocity, max_rotation_velocity) # Degrees per tick
        if self.rotation_speed == 0:                        # No rotation would look boring.
            self.rotation_speed = 1

        vertex_count = 12                                   # Number of vertices that will make up this rock.
        slice_size = 360 / vertex_count                     # Good for this to be an integer.

        for v_num in range(vertex_count):
            if self.size == "Large":
                vertex = [0, self.radius + random.randint(-15, 15)]
            elif self.size == "Medium":
                vertex = [0, self.radius + random.randint(-7, 7)]
            else:
                vertex = [0, self.radius + random.randint(-5, 5)]

            vertex = cc.rotate_around_origin(vertex, slice_size * v_num)
            self.vertices.append(vertex)

        self.kill = False                                   # Should this rock be killed off?
        self.collision = False                              # Has the rock collided with something?
        self.exploding = False                              # Is the rock in the process of exploding?
        self.explosion_step = 0                             # Current step of explosion animation.

        self.colour = (random.randint(60, 200), random.randint(60, 200), random.randint(60, 200))

        trace(config, self.size + ' rock created.')           # Send trace info to stdout.

    def place_on_side_of_screen(self, config):

        start_side = random.randint(1, 4)                   # 1=Top, 2=Bottom, 3=Left, 4=Right
        assert start_side in [1, 2, 3, 4]

        if start_side == 1:                                 # From the top of screen.
            # TODO Try simplifying the first two in same style as second two.

            self.coords = [random.randint(config.border, config.screen_size[0] - config.border), config.top_dead]

            if self.coords[0] <= config.screen_size[0] / 2:    # Left hand side of top of screen.
                self.drift = [10 * random.randint(1, 3) / config.target_fps,
                              10 * random.randint(2, 4) / config.target_fps]   # So drift rightwards and downwards.
            else:
                self.drift = [10 * random.randint(-3, -1) / config.target_fps,
                              10 * random.randint(2, 4) / config.target_fps]     # Otherwise drift leftwards and downwards.

        if start_side == 2:                                 # Bottom
            self.coords = [random.randint(config.border, config.screen_size[0] - config.border), config.bottom_dead]

            if self.coords[0] <= config.screen_size[0] / 2:    # Left hand side of top of screen.
                self.drift = [10 * random.randint(1, 3) / config.target_fps,
                              10 * random.randint(-4, -2) / config.target_fps]   # So drift rightwards and upwards.
            else:
                self.drift = [random.randint(-3, -1), random.randint(-4, -2)]     # Otherwise drift leftwards and upwards.

        if start_side == 3:
            self.coords = [-100, random.randint(200, 400)]
            self.drift = [10 * random.randint(2, 4) / config.target_fps,
                          10 * random.randint(-3, 3) / config.target_fps]

        if start_side == 4:
            self.coords = [900, random.randint(200, 400)]
            self.drift = [10 * random.randint(-4, -2) / config.target_fps,
                          10 * random.randint(-3, 3) / config.target_fps]

    # Has the rock strayed outside of the game screen? If so, it is flagged to be killed off.
    def check_onscreen(self, config):
        if (self.coords[0] < config.left_dead
                or self.coords[0] > config.right_dead
                or self.coords[1] < config.top_dead
                or self.coords[1] > config.bottom_dead):
            self.kill = True

    # Is the parm vertex inside the rock?
    def check_collision(self, vertex):
        # TODO Try omitting this line of code, as this attribute was set to False when object created.
        self.collision = False                      # Start by assuming that vertex is outside all triangles.

        # Before doing the triangle analysis (which is time consuming), do a simpler clipping test.
        # Imagine a square around the centre of the rock. Is the vertex inside that square?
        if (vertex[0] > self.coords[0] - self.radius - 15       # 15 is the most that can randomly be added to a vertex
        and vertex[0] < self.coords[0] + self.radius + 15       # at the time that the rock was created.
        and vertex[1] > self.coords[1] - self.radius - 15
        and vertex[1] < self.coords[1] + self.radius + 15):

            # If the vertex is inside the square, then it is worth checking each triangle that makes up the
            # rock in turn, to see if the vertex is inside any of them.
            prev_vertex = self.vertices[-1]  # This is so we have 3 points for first triangle.

            for triangle_vertex in self.vertices:
                if cc.is_inside_triangle(vertex, self.position(prev_vertex), self.position(triangle_vertex), self.coords):
                    self.collision = True
                prev_vertex = triangle_vertex

    # Apply some transformations to calculate the coordinates of the rock's parm vertex on the game screen.
    def position(self, vertex):
        rotated = cc.rotate_around_origin(vertex, self.rotation)
        return cc.translation(rotated, self.coords)

    # Begin the process of exploding this rock.
    def explode(self, config):
        self.exploding = True                               # Flag it as exploding.
        config.explosion_channel.play(config.explosion_sound)   # Play explosion sound.

    # Continue animation of rock's explosion.
    def animate_explosion(self, game):
        if self.explosion_step < game.config.target_fps:           # Higher FPS mean, more animation steps for explosion!
            self.explosion_step += 1
        else:
            self.kill = True                                # Explosion animation is over, so kill off the rock.

        # Half way through the explosion animation, maybe spawn new rocks.
        if self.explosion_step == int(0.5 * game.config.target_fps):
            if self.size in ['Large', 'Medium']:
                for i in range(2):                          # range(2), because 2 child rocks will be created.
                    if self.size == 'Large':
                        new_rock = Rock(game.config, 'Medium')
                    else:
                        new_rock = Rock(game.config, 'Small')

                    # Give it position that is near it's parent.
                    new_rock.coords = cc.translation(self.coords, [random.randint(-25, 25), random.randint(-25, 25)])

                    # New rocks's drift will be similar to parent.
                    # TODO I think this is cause of some child rocks being stationary...
                    # TODO Need to add some check 'if near to zero, then set to 1'
                    new_drift_x = self.drift[0] + 10 * random.randint(-1, 1) / game.config.target_fps
                    new_drist_y = self.drift[1] + 10 * random.randint(-1, 1) / game.config.target_fps

                    new_rock.drift = [new_drift_x, new_drist_y]

                    game.rocks.append(new_rock)             # Add the new rocks to the game.

    # Draw this rock on game screen.
    def draw(self, config):
        # TODO Make the normal rock display, and exploding rock display be separate methods.

        prev_vertex = self.vertices[-1]                     # This will make it a complete polygon.

        for vertex in self.vertices:
            if not self.exploding:
                if config.monochrome:
                    pygame.draw.line(config.screen, config.WHITE, self.position(prev_vertex), self.position(vertex), 1)

                # TODO Refactor to draw whole polygon in one go, rather than drawing a number of triangles.
                else:
                    triangle = []
                    triangle.append(self.position(prev_vertex))
                    triangle.append(self.position(vertex))
                    triangle.append(self.coords)
                    pygame.draw.polygon(config.screen, self.colour, triangle, 0)

            else:
                # Higher FPS mean more explosion steps, so lower speed of explosion per step.
                scaled_vertex = cc.scale(vertex, 5 * self.explosion_step / config.target_fps)
                [x, y] = self.position(scaled_vertex)

                # TODO Use the function in cartesian coordinate package to make coords integers.
                if config.monochrome:
                    pygame.draw.circle(config.screen, config.WHITE, [int(x), int(y)], 1, 1)
                else:
                    pygame.draw.circle(config.screen, self.colour, [int(x), int(y)], 4, 4)

                # TODO Make the ship explosion particle randomly twinkle away.
                # if random.randint(1, 25) == 10:
                #     self.explosion_vertices.remove(v)

            prev_vertex = vertex

    # Move the rock by one tick.
    def move(self):
        self.rotation += self.rotation_speed
        self.coords = cc.translation(self.coords, self.drift)


############################################
# BULLET
############################################

class Bullet:
    def __init__(self, origin, angle, colour):

        self.coords = origin                                        # Current [x, y] coordinates of the bullet.
        self.angle = angle                                          # Angle that the bullet is moving in.
        self.colour = colour                                        # Colour of bullet. Will be same as player's ship.

        self.drift = cc.rotate_around_origin([0, 20], self.angle)   # Incremental drift this bullet will do each tick.
        self.kill = False                                           # Flags is this bullet is to be deleted.

    # Draw the bullet as a little circle on the game screen.
    def draw(self, config):
        if config.monochrome:
            pygame.draw.circle(config.screen, config.WHITE, cc.integer_coord(self.coords), 1, 1)
        else:
            pygame.draw.circle(config.screen, self.colour, cc.integer_coord(self.coords), 2, 2)

    # Move the bullet by one tick.
    def move(self):
        self.coords = cc.translation(self.coords, self.drift)

    # Is the bullet still onscreen? If not, flag it to be killed.
    def check_onscreen(self, config):
        if (self.coords[0] < config.left_dead
                or self.coords[0] > config.right_dead
                or self.coords[1] < config.top_dead
                or self.coords[1] > config.bottom_dead):
            self.kill = True


############################################
# SPACE SHIP
############################################

class SpaceShip:

    def __init__(self, origin, colour):

        self.coords = origin                                        # Starting location of ship is parm origin.
        self.colour = colour                                        # Colour of the ship.

        self.rotation = 0                                           # Direction that ship is pointing. In degrees.
        self.exploding = False                                      # Is the ship exploding?
        self.explosion_step = 0                                     # Current step in explosion animation.
        self.kill = False                                           # Is the ship flagged to be deleted?
        self.remaining_invincibility_ticks = 0

        # The vertex is the nose of the ship, where bullets are fired from.
        self.vertices = [[0, 10], [-5, -5], [0, 0], [5, -5]]

        explosion_vertex_count = 72                                    # Number of vertices that will make up explosion.
        slice_size = 360 / explosion_vertex_count                     # Good for this to be an integer.
        self.explosion_vertices = []

        for v_num in range(explosion_vertex_count):
            vertex = [0, 7.0 + random.randint(-2, 2)]

            vertex = cc.rotate_around_origin(vertex, slice_size * v_num)
            self.explosion_vertices.append(vertex)

        self.bullets = []                       # Bullets in flight will be appended to this list when they are fired.

    # Rotate the ship clockwise by 10 degrees.
    def rotate_clockwise(self):
        if not self.exploding:              # Exploding ships can't rotate!
            self.rotation -= 10             # In Pygame, increased y coord is down, hence this rotation is -ve.

    # Rotate the ship anticlockwise by 10 degrees.
    def rotate_anticlockwise(self):
        if not self.exploding:              # Exploding ships can't rotate!
            self.rotation += 10            # In Pygame, increased y coord is down, hence this rotation is +ve.

    # If ship is not currently exploding, then fire a bullet from its nose.
    def fire_bullet(self, config):
        if len(self.bullets) < 10 and not self.exploding:
            # Bullets should originate from the ships nose.
            # Vertex 0 of the ship is it's nose.
            ship_nose = self.position(self.vertices[0])
            self.bullets.append(Bullet(ship_nose, self.rotation, self.colour))

            config.laser_channel.play(config.laser_sound)

    # Calculate position of parm ship vertex in game screen coordinates.
    def position(self, vertex):
        rotated = cc.rotate_around_origin(vertex, self.rotation)
        return cc.translation(rotated, self.coords)

    def draw(self, config):
        # TODO Refactor to have separate methods for drawing ship and drawing exploding ship.

        prev_vertex = self.vertices[-1]  # This will make it a complete polygon.

        if not self.exploding:
            for vertex in self.vertices:
                if config.monochrome:
                    pygame.draw.line(config.screen, config.WHITE, self.position(prev_vertex), self.position(vertex), 1)

                # TODO refactor to draw whole polygon in one go, rather than drawing a number of triangles.
                else:
                    triangle = []
                    triangle.append(self.position(prev_vertex))
                    triangle.append(self.position(vertex))
                    triangle.append(self.coords)
                    pygame.draw.polygon(config.screen, self.colour, triangle, 0)

                prev_vertex = vertex

        else:
            for v in self.explosion_vertices:
                scaled_vertex = cc.scale(v, 5 * self.explosion_step / config.target_fps)
                [x, y] = cc.translation(scaled_vertex, self.coords)

                if config.monochrome:
                    pygame.draw.circle(config.screen, config.WHITE, [int(x), int(y)], 1, 1)
                else:
                    pygame.draw.circle(config.screen, self.colour, [int(x), int(y)], 4, 4)

                # Make the ship explosion particle randomly twinkle away.
                if random.randint(1, 100) == 50:
                    self.explosion_vertices.remove(v)

    # Begin the explosion of the ship.
    def explode(self, config):
        self.exploding = True  # Start exploding the ship.
        config.ship_explosion_channel.play(config.ship_explosion_sound)

    def animate_explosion(self, config):
        if self.explosion_step < 4 * config.target_fps:    # Higher FPS mean, more animation steps for explosion!
            self.explosion_step += 1
        else:
            self.kill = True                        # Explosion animation is over, so kill off the rock.


############################################
# PLAYER
############################################

class Player:

    def __init__(self, player_name, colour, origin):

        self.player_name = player_name          # For example, 'Player 1'.
        self.colour = colour                    # Colour of player's ship, bullets and score [r, g, b].
        self.origin = origin                    # Starting coordinates for player's ship [x, y].

        self.score = 0                          # Number of points that he's scored.
        self.ship = SpaceShip(origin, colour)   # This player's spaceship.

    def killed_a_rock(self, size):
        if size == 'Large':
            self.score += 10
        elif size == 'Medium':
            self.score += 20
        else:                                   # Small rocks are hard to hit, hence they score 30 points.
            self.score += 30

    def lost_a_spaceship(self):
        origin = self.ship.coords
        colour = self.ship.colour
        self.ship = SpaceShip(origin, colour)   # Replace the killed spaceship with a new one.
        self.score -= 100


############################################
# GAME
############################################

class Game:

    def __init__(self, config):

        self.config = config

        # Create some rocks for start of game.
        self.num_rocks = 20                             # Target number of rocks to have on screen at once.
        self.rocks = []
        for r in range(self.num_rocks):
            new_rock = Rock(self.config, 'Large')
            new_rock.place_on_side_of_screen(self.config)
            self.rocks.append(new_rock)

        assert self.config.num_players in [1, 2]
        self.players = []                               # List of players.
        for n in range(self.config.num_players):
            player_name = 'Player ' + str(n + 1)        # players[0] is called 'Player 1', etc.

            if n == 0:
                colour = self.config.RED                       # First player has a red ship.
            else:
                colour = self.config.GREEN                     # Second player has a green ship.

            if self.config.num_players == 1:                   # If only one player, she can be in centre of screen.
                origin = self.config.screen_centre
            else:
                origin_y = self.config.screen_centre[1]
                screen_width = self.config.screen_size[0]

                if n == 0:
                    # For 2 player game, first player is moved a bit to the left.
                    origin_x = self.config.screen_centre[0] - int(screen_width / 4)
                else:
                    # For 2 player game, second player is moved a bit to the right.
                    origin_x = self.config.screen_centre[0] + int(screen_width / 4)

                origin = [origin_x, origin_y]

            self.players.append(Player(player_name, colour, origin))    # Add each player to the list of players.

        self.game_end_time = time.time() + 60                   # '60' is the length of the game in seconds.

    def draw_text(self, text, x, y, colour):
        textsurface = self.config.myfont.render(text, False, colour)
        self.config.screen.blit(textsurface, (x, y))

    def draw_centred_white_text(self, text, position, y):
        assert position in ['Centre', 'Left', 'Right']

        pixels_per_char = 12                    # Width of 1 char of text of screen in Courier font.
        if position == "Centre":
            self.draw_text(text,
                           int(self.config.screen_centre[0] - pixels_per_char * len(text) / 2),
                           y,
                           self.config.WHITE)
        elif position == "Left":
            self.draw_text(text,
                           int(self.config.screen_size[0] * 0.25 - pixels_per_char * len(text) / 2),
                           y,
                           self.config.WHITE)
        else:
            self.draw_text(text,
                           int(self.config.screen_size[0] * 0.75 - pixels_per_char * len(text) / 2),
                           y,
                           self.config.WHITE)

    # Draw the frames per second at the bottom left of the screen.
    def draw_fps(self):
        self.draw_text('FPS = ' + str(round(self.config.clock.get_fps())),
                       10, self.config.screen_size[1] - 45, self.config.WHITE)

    def draw_game_info(self):
        # Always draw first player's score, as there is always at least 1 player.
        if self.config.monochrome:
            c1 = self.config.WHITE
            c2 = self.config.WHITE
        else:
            c1 = self.players[0].colour
            if self.config.num_players ==2:
                c2 = self.players[1].colour

        self.draw_text(self.players[0].player_name + ': ' + str(self.players[0].score), 10, 10, c1)

        if self.config.num_players == 2:
            self.draw_text(self.players[1].player_name + ': ' + str(self.players[1].score),
                                  self.config.screen_size[0] - 200,
                                  10,
                                  c2)

        if not self.config.demo_mode:
            self.draw_centred_white_text('Time: ' + str(round(self.game_end_time - time.time())), 'Centre', 10)

    # Draw instruction on screen during demo mode.
    def draw_demo_info(self):
        self.draw_centred_white_text('GAME OVER', 'Centre', self.config.screen_centre[1] - 150)
        self.draw_centred_white_text('Press 1 for 1 player game', 'Centre', self.config.screen_centre[1] - 100)
        self.draw_centred_white_text('Press 2 for 2 player game', 'Centre', self.config.screen_centre[1] - 75)

        self.draw_centred_white_text('Player 1', 'Left', self.config.screen_centre[1] + 50)
        self.draw_centred_white_text('Z = Rotate anticlockwise', 'Left', self.config.screen_centre[1] + 75)
        self.draw_centred_white_text('X = Rotate clockwise', 'Left', self.config.screen_centre[1] + 100)
        self.draw_centred_white_text('A = Fire gun', 'Left', self.config.screen_centre[1] + 125)

        self.draw_centred_white_text('Player 2', 'Right', self.config.screen_centre[1] + 50)
        self.draw_centred_white_text('← = Rotate anticlockwise', 'Right', self.config.screen_centre[1] + 75)
        self.draw_centred_white_text('→ = Rotate clockwise', 'Right', self.config.screen_centre[1] + 100)
        self.draw_centred_white_text('/ = Fire gun', 'Right', self.config.screen_centre[1] + 125)

    # This one method does the drawing of all of the graphical elements in the game.
    def draw_all_elements(self):
        # Clear the screen and set the screen background.
        self.config.screen.fill(self.config.BLACK)

        for r in self.rocks:                    # Draw each rock.
            r.draw(self.config)

        # Loop through all of the players, drawing their ships, and their ship's bullets.
        for p in self.players:
            p.ship.draw(self.config)                       # Draw the player's space ship.

            for b in p.ship.bullets:                  # Draw each bullet.
                b.draw(self.config)

        self.draw_game_info()

        if self.config.demo_mode:
            self.draw_demo_info()

        # If in debug mode, draw the frames per second onscreen.
        if self.config.debug:
            self.draw_fps()

        pygame.display.flip()

    # Take a screenshot. Save it in the 'screenshots' folder.
    def take_screenshot(self):
        screenshot_name = 'screenshots/screenshot' + format(self.config.screenshot_num, '04') + '.png'
        pygame.image.save(self.config.screen, screenshot_name)
        self.config.screenshot_num += 1

    # Act on key presses bu game players.
    def key_handling(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_z]:
            self.players[0].ship.rotate_anticlockwise()
        if keys[pygame.K_x]:
            self.players[0].ship.rotate_clockwise()
        if keys[pygame.K_a]:
            self.players[0].ship.fire_bullet(self.config)       # Need config, as it contains the bullet firing sound.

        if self.config.num_players == 2:
            if keys[pygame.K_LEFT]:
                self.players[1].ship.rotate_anticlockwise()
            if keys[pygame.K_RIGHT]:
                self.players[1].ship.rotate_clockwise()
            if keys[pygame.K_SLASH]:
                self.players[1].ship.fire_bullet(self.config)   # Need config, as it contains the bullet firing sound.

        if keys[pygame.K_g]:
            self.take_screenshot()

        if keys[pygame.K_ESCAPE]:
            return True
        else:
            return False

    # Do one tick of the game logic and drawing to screen, etc.
    # If in demo mode, collision detection will be skipped.
    def animate_1_tick(self):
        # Ensure that the game ticks do not exceed the target FPS.
        self.config.clock.tick(self.config.target_fps)

        for p in self.players:
            # If player ship exploding, do the next step of the explosion animation.
            if p.ship.exploding:
                p.ship.animate_explosion(self.config)

            if p.ship.kill:
                p.lost_a_spaceship()

            for b in p.ship.bullets:
                b.move()
                b.check_onscreen(self.config)
                if b.kill:
                    p.ship.bullets.remove(b)
                    trace(self.config, 'Bullet removed, bullets left for ' +
                          p.player_name + ' =' + str(len(p.ship.bullets)))

        for r in self.rocks:
            r.move()
            r.check_onscreen(self.config)

            # Check whether this rock has been hit by a bullet.
            if not r.exploding:
                for p in self.players:

                    # In demo mode, don't check for collisions.
                    if not self.config.demo_mode:
                        for b in p.ship.bullets:
                            r.check_collision(b.coords)
                            if r.collision:
                                r.explode(self.config)
                                b.kill = True  # This bullet has killed a rock, so it must be killed itself too.
                                p.killed_a_rock(r.size)

            # In demo mode, don't check for collisions.
            if not r.exploding and not self.config.demo_mode:
                for p in self.players:
                    if not p.ship.exploding:

                        r.check_collision(p.ship.coords)
                        if r.collision:  # The rock hit the ship.
                            r.explode(self.config)  # Start exploding the rock.
                            p.ship.explode(self.config)

            # If this rock is exploding, do the steps of the explosion animation - including possibly, creating
            # child rocks.
            if r.exploding:
                r.animate_explosion(self)

            if r.kill:
                if r.exploding:  # Must have collided with something.
                    # If we are getting low on rocks, then create a new large rock.
                    if len(self.rocks) <= self.num_rocks:
                        new_rock = Rock(self.config, 'Large')
                        new_rock.place_on_side_of_screen(self.config)
                        self.rocks.append(new_rock)

                else:  # Must be getting killed due to being at edge of screen.
                    # Make new rock. Same size as one that is about to be removed.
                    new_rock = Rock(self.config, r.size)
                    new_rock.place_on_side_of_screen(self.config)
                    self.rocks.append(new_rock)

                self.rocks.remove(r)  # Rock is to be killed, so remove it from the list of rocks.

                trace(self.config, r.size + ' rock removed, rocks left=' + str(len(self.rocks)))

        self.draw_all_elements()

    # Actually play the game.
    def play(self):
        done = False
        self.config.demo_mode = False           # This is not a demo, this is the real game.
        self.config.monochrome = False          # Actual games are in colour.

        # Loop until the user clicks the close button, or game time is up.
        while not done:
            for event in pygame.event.get():    # User did something
                if event.type == pygame.QUIT:   # If user clicked close
                    self.config.quit = True
                    done = True                 # Flag that we are done so we exit this loop

            # Out of time?
            if time.time() >= self.game_end_time:
                done = True

            escape_pressed = self.key_handling()
            if escape_pressed:
                done = True

            self.animate_1_tick()


############################################
# CONFIG
############################################

class Config:

    def __init__(self, debug, target_fps):

        self.debug = debug                  # True=logging sent to stdout, and current FPS displayed on screen.
        self.target_fps = target_fps        # Some game animations use target Frames Per Second to control their pace.

        self.monochrome = True              # True=old style graphics used for rocks, etc.
        self.num_players = 1

        self.demo_mode = True
        self.quit = False                   # Will become true when the use chooses to quit the game.

        pygame.init()                       # Initialize the game engine.

        # Define the colors we will use in RGB format.
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = [255, 0, 0]
        self.GREEN = [0, 255, 0]

        # Set the height and width of the viewport.
        self.screen_size = [800, 600]
        self.screen_centre = [int(self.screen_size[0] / 2), int(self.screen_size[1] / 2)]
        self.screen = pygame.display.set_mode(self.screen_size)

        self.clock = pygame.time.Clock()

        # Start the Pygame text rendering system.
        pygame.font.init()
        self.myfont = pygame.font.SysFont('Courier New', 20)

        pygame.display.set_caption('Space Rocks')   # The game window title.

        # Start the Pygame sound system.
        pygame.mixer.init()
        pygame.mixer.set_num_channels(3)            # One channel for laser gun fires, one for explosions.

        # Get some game sounds ready, and allocate sound channels for them.
        self.explosion_sound = pygame.mixer.Sound('assets/110115__ryansnook__small-explosion.wav')
        self.laser_sound = pygame.mixer.Sound('assets/341235__sharesynth__laser01.wav')
        self.ship_explosion_sound = pygame.mixer.Sound('assets/235968__tommccann__explosion-01.wav')
        self.explosion_channel = pygame.mixer.Channel(0)
        self.laser_channel = pygame.mixer.Channel(1)
        self.ship_explosion_channel = pygame.mixer.Channel(2)

        # Border greater than width of largest possible rock. This ensures that when a rock is removed for being
        # outside of the screen plus border, we can be sure that all of the rock is off screen. If the border wasn't
        # wide enough rocks that are drifting off screen could be removed while part of them is still onscreen.
        self.border = 100

        # These are the edges of the zone where graphical objects are born and die.
        self.left_dead = - self.border
        self.top_dead = -self.border
        self.right_dead = self.screen_size[0] + self.border
        self.bottom_dead = self.screen_size[1] + self.border

        self.screenshot_num = 1                         # Number of screenshots taken.

    def choose_options(self):
        this_game = Game(self)

        while not self.quit:
            for event in pygame.event.get():  # User did something
                if event.type == pygame.QUIT:  # If user clicked close
                    self.quit = True  # Flag that we are done so we exit this loop, and quit the game

            keys = pygame.key.get_pressed()

            if keys[pygame.K_1]:                # '1' key starts a one player game.
                self.num_players = 1
                this_game = Game(self)
                this_game.play()
                self.demo_mode = True
                self.monochrome = True          # Demo mode is monochrome.

            if keys[pygame.K_2]:                # '2' key starts a two player game.
                self.num_players = 2
                this_game = Game(self)
                this_game.play()
                self.demo_mode = True
                self.monochrome = True          # Demo mode is monochrome.

            if keys[pygame.K_g]:
                this_game.take_screenshot()

            if not self.quit:
                this_game.animate_1_tick()

        # Be IDLE friendly.
        pygame.quit()
