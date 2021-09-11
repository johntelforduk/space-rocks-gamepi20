# Program to check that combinations of keys used in game can be detected OK if pressed at same time.

import pygame                           # 2d games engine.

# Initialize the game engine.
pygame.init()
screen = pygame.display.set_mode([200, 100])
clock = pygame.time.Clock()

# Loop until the user clicks the close button.
done = False

while not done:
    clock.tick(5)                      # Loop at no more than 10 times per second.

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        print('Left ')
    if keys[pygame.K_RIGHT]:
        print('Right ')
    if keys[pygame.K_SLASH]:
        print('Slash ')

    if keys[pygame.K_z]:
        print('Z')
    if keys[pygame.K_x]:
        print('X')
    if keys[pygame.K_a]:
        print('A')

    print('-----')

pygame.quit()
