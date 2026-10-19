// Tests d'ÉCRAN par rôle — code FIXE : chaque app reçoit ses propres tests, sans qu'on en écrive un seul.
// (N1.3) découpé comme le testeur des règles : le NOYAU (e2e/noyau.ts : attentes tirées de la matrice
// d'origine, connexion, gestes communs) et un MODULE PAR BLOC (e2e/blocs/). Ce fichier ne fait que les
// jouer, dans l'ordre où ils s'appuient les uns sur les autres (on crée avant de faire évoluer, modifier,
// supprimer). Un nouveau bloc = un nouveau module, ajouté ici — sans toucher aux autres.
import { test } from '@playwright/test';
import { circuit } from './blocs/circuit';
import { creer } from './blocs/creer';
import { enfants } from './blocs/enfants';
import { menu } from './blocs/menu';
import { modifier } from './blocs/modifier';
import { profil } from './blocs/profil';
import { supprimer } from './blocs/supprimer';

test.describe.configure({ mode: 'serial' });

menu();        // 0-1. menu de chaque rôle, boutons « Nouveau… » et de création d'un clic
creer();       // 2. chaque fiche se crée par son formulaire
enfants('parent au départ');      // 2b. (N1.3) les lignes, dans la page de leur parent…
circuit();     // 3. chaque circuit, parcouru état après état
enfants('parent avancé');         // 3b. … et à nouveau quand le circuit a fait avancer le parent
modifier();    // 4. modifier selon l'état
supprimer();   // 5. supprimer selon l'état ; intégrité
profil();      // 6. un profil par rôle
