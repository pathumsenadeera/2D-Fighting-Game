# Naruto vs Sasuke: A Multimedia Fighting Game

## Project Overview

### Project Title and Description
Naruto vs Sasuke is an interactive 2D fighting game developed using Python and the Pygame library. Players control Naruto or Sasuke in a battle featuring melee attacks, fireball projectiles, jumping mechanics, and health tracking. The game includes sound effects for attacks, hits, and shooting, background music, animated sprites, and selectable map backgrounds (forest, village, arena). It demonstrates multimedia concepts such as graphics rendering, audio processing, animation, and real-time user interaction.

### Objectives
- Demonstrate practical implementation of multimedia technologies, including sprite animation, sound integration, and graphical user interfaces.
- Showcase audio-visual synchronization, image processing for scaling and flipping sprites, and interactive gameplay elements.
- Provide an engaging application that highlights real-time multimedia processing.

### Target Users
This game targets anime enthusiasts, particularly fans of the Naruto series, as well as students and developers interested in game development and multimedia applications.

### Technology Stack
- Programming Language: Python 3.12.3
- Libraries:
  - Pygame: For game development, graphics rendering, sound effects, and user input handling.
  - NumPy: For image processing in sprite sheet loading.
  - Pillow (PIL): For converting and manipulating images in sprite sheets.
- Tools: Visual Studio Code for development, GitHub for version control.

## Installation Instructions

1. **Clone the Repository**:
   ```
   git clone <repository-url>
   cd NarutoGame
   ```

2. **Install Dependencies**:
   Ensure Python 3.6 or later is installed. Install required libraries using the provided `requirements.txt`:
   ```
   pip install -r requirements.txt
   ```
   The `requirements.txt` includes:
   ```
   pygame>=2.6.0
   numpy>=1.26.4
   pillow>=10.4.0
   ```

3. **Asset Setup**:
   Ensure the `asset` folder is present with the following structure:
   ```
   asset/
   ├── sprites/
   │   ├── sheet.png  (Naruto spritesheet)
   │   └── sheet2.png (Sasuke spritesheet)
   ├── sounds/
   │   ├── attack.wav
   │   ├── hit.wav
   │   ├── shoot.wav
   │   └── bg_loop.wav
   ├── fireball/
   │   ├── image0.png
   │   └── ... (up to image76.png)
   ├── forest.jpg
   ├── village.jpg
   ├── arena.jpg
   └── game_music.mp3
   ```

## Usage

Run the game with:
```
python naruto_vs_sasuke.py
```

- Select a map (1-3 for Forest, Village, Arena) and press Enter to start.
- Use +/- keys to resize sprites during gameplay.
- Press R to restart after a game over.

## Controls
- **Naruto** (Player 1):
  - Move Left/Right: Arrow Left/Right
  - Jump: Arrow Up
  - Melee Attack: Arrow Down
  - Shoot Fireball: Right Ctrl
- **Sasuke** (Player 2):
  - Move Left/Right: A/D
  - Jump: W
  - Melee Attack: S
  - Shoot Fireball: Left Ctrl

## Multimedia Features
- **Graphics and Animation**: Sprite sheets for character animations (idle, walk, attack, jump) with autoscan loading and runtime scaling.
- **Audio**: Background music (`game_music.mp3`), sound effects for attacks, hits, and shooting, with fallback synthetic sounds.
- **Interactivity**: Real-time collision detection for melee and projectiles, health bars, and leaderboard.
- **Maps**: Selectable backgrounds with image scaling for different screen sizes.

## Group Members and Contributions

| Team Member | Registration No. | Index No. | Contribution |
|-------------|------------------|-----------|--------------|
| 1          | ICT/2022/001    | 5609    | Game logic, character movement, and collision detection |
| 2          | ICT/2022/008    | 5616     | Audio integration, sound effects, and background music |
| 3          | ICT/2022/050    | 5656     | Sprite animation, image processing, and scaling features |
| 4          | ICT/2022/113   | 5715    | User interface, map selection, and health bar implementation |
| 5          | ICT/2022/120   | 5722  | Projectile mechanics, fireball animation, and testing |

(Replace placeholders with actual group member details.)

## Challenges and Solutions
- **Challenge**: Dynamic asset loading across different systems.
  - **Solution**: Used `os.path` for relative paths to ensure portability.
- **Challenge**: Sprite sheet processing for animations.
  - **Solution**: Implemented autoscan and grid loading with Pillow and NumPy for efficient frame extraction.
- **Challenge**: Audio synchronization and fallbacks.
  - **Solution**: Used Pygame mixer with synthetic sound generation as backups.

## Learning Outcomes
Through this project, we mastered multimedia concepts such as audio playback, image manipulation, animation rendering, and real-time interaction using Pygame. We also learned about collaborative development on GitHub and handling dependencies.

## Potential Improvements
- Add multiplayer over network.
- Include more characters and power-ups.
- Implement AI for single-player mode.
- Enhance graphics with particle effects.

## Reflection
This project provided valuable hands-on experience in multimedia application development, reinforcing our understanding of Python libraries for game creation. Collaboration among group members ensured a well-rounded implementation.
