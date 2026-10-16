# text based game

- Maintained isolated game state per user by routing all interactions through /arrive and /depart lifecycle handlers, which instantiate and destroy private game copies on demand, eliminating cross-user state leakage and enabling simultaneous gameplay without interference in a shared distributed environment.
- Architected a depth-based item hosting and scoring system (levels 0/1/2) with granular ownership tracking, allowing players to discover, carry, and deposit items across domains, while a central hub coordinates cross-domain item transfers and global completion status for a persistent, puzzle-driven multiplayer adventure.
- Optimized state synchronization by minimizing inter-node communication through local state snapshots and lazy persistence, reducing network overhead and supporting horizontal scaling as concurrent user count grows.
