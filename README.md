# NEAT Dino Game 🦕

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Library](https://img.shields.io/badge/library-pygame-yellow.svg)
![Algorithm](https://img.shields.io/badge/algorithm-NEAT-orange.svg)

An autonomous AI agent trained to play a custom-built, pixel-art version of the Chrome Dinosaur Game. The agent utilizes **NeuroEvolution of Augmenting Topologies (NEAT)** to evolve its own neural network architecture and decision-making logic through Darwinian natural selection.

<img width="1546" height="544" alt="Screenshot 2026-03-26 053510" src="https://github.com/user-attachments/assets/fd82f7a0-305f-4039-9ef4-5e7f08a5e822" />

---

## How It Works: The NEAT Algorithm

The core of this project is the **NEAT (NeuroEvolution of Augmenting Topologies)** algorithm. Unlike standard deep learning that only optimizes weights in a fixed structure, NEAT evolves both the **weights** and the **topology** (the connections and number of neurons) of the neural network.

### 1. Evolutionary Logic
1.  **Population:** Every generation starts with 150-250 "Dinos," each with a unique, randomized neural network.
2.  **Evaluation:** Each agent is placed in the game environment. Its performance determines its "Fitness Score."
3.  **Speciation:** Agents are grouped into species based on genetic similarity. This prevents high-performing structures from being lost too early and encourages niche exploration.
4.  **Selection & Crossover:** The best-performing Dinos are selected to "reproduce." Their genetic information is combined to create a new generation.
5.  **Mutation:** Random changes occur (adding a new connection, adding a neuron, or modifying a weight) to discover new survival strategies.

### 2. Neural Network Architecture

#### **Inputs (5 Sensors)**
The AI "sees" the game state through 5 normalized parameters:
*   **Relative Y:** The Dino’s vertical distance from the ground.
*   **Distance to Obstacle:** Horizontal distance to the nearest upcoming cactus.
*   **Obstacle Height:** The height of the incoming obstacle.
*   **Game Speed:** The current velocity of the environment.
*   **Vertical Velocity ($v_y$):** Whether the Dino is currently rising or falling.

#### **Output (1 Action)**
*   **Jump Trigger:** A single output neuron with a `tanh` activation function. If the output exceeds a predefined threshold (e.g., `> 0.5`), the Dino performs a jump.

---

## 🏆 Fitness Function Strategy 

The success of the agent depends on a carefully designed fitness function that rewards efficiency and punishes "spamming":

*   **Survival Reward:** Small incremental points for every frame the Dino stays alive.
*   **Obstacle Clearance:** A significant reward (+40.0) for every obstacle successfully cleared.
*   **Proactive Penalties:** A penalty is applied if the agent jumps when no obstacle is near, forcing it to learn **precision timing**.
*   **Collision Penalty:** A negative score is applied upon collision to ensure the genetic line of "dangerous" Dinos is terminated.

---

## Installation & Usage

### Prerequisites
*   Python 3.8+
*   `pygame`
*   `neat-python`

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/sonamansuryan/neat-dino.git
   cd neat-dino
   ```
2. Install dependencies:
   ```bash
   pip install pygame neat-python
   ```

### Running the Project
*   **To start training:** 
    ```bash
    python main.py
    ```
*   **Configuration:** You can modify `config-feedforward.txt` to change the population size, mutation rates, or fitness threshold (currently set to 3000).

---

## Visuals
*   **Pixel Art:** All sprites (Dino, Cacti, Clouds) are custom-rendered using logical pixel-rects in Pygame, requiring no external image assets.
*   **Real-time HUD:** Displays current Generation, Number of Survivors, Current Speed, and the High Score.
*   **Neural Visualization:** High-performing Dinos feature a visual indicator showing the activation level of their output neuron.

---

### Acknowledgments
*   Inspired by the original Chrome Dino game.
*   Built using the `neat-python` library by Kenneth O. Stanley and others.
