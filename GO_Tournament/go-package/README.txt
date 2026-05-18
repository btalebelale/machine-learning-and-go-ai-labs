========================================
  TP GO - Joueur IA
  Binome : Mohamed Kraimy & Bella Taleb El Alem
  Enseirb-Matmeca - Bordeaux INP - 2025/2026
========================================

STRATEGIE :
  Notre joueur utilise :
  - Negamax avec elagage Alpha-Beta
  - Iterative Deepening (profondeur 1->20, limitee par le temps)
  - Transposition Table (evite de recalculer les positions deja vues)
  - Aspiration Windows (fenetres etroites autour du score precedent)
  - Ordonnancement des coups : captures > centre > coup TT

  Heuristique d'evaluation :
  - Territoire (chinese scoring)  x4
  - Pierres capturees             x8
  - Atari (groupes a 1 liberte)   x15
  - Difference de libertes        x1
  - Yeux                          x3

  Gestion du temps (budget 45 min total) :
  - Early game (< 15 coups) : 10s/coup
  - Mid game   (15-45 coups) : 35s/coup
  - Late game  (> 45 coups)  : 55s/coup
