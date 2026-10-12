# The Quiet Adventure

Le site de nos carnets de voyage, [thequietadventure.com](https://thequietadventure.com), en français et en anglais.

C'est un site statique : chaque récit est un simple fichier, le site est reconstruit et publié automatiquement par GitHub à chaque modification. Pas de WordPress, pas de base de données, pas d'abonnement.

## Mise en service (une seule fois)

1. **Activer GitHub Pages** : *Settings › Pages › Build and deployment › Source* : choisir **GitHub Actions**.
2. **Rapatrier les photos** : onglet *Actions* › « Rapatrier les photos depuis WordPress » › *Run workflow*. Le script copie toutes les photos et vidéos des récits dans `media/` (compter 20 à 40 minutes). **À faire tant que le domaine pointe encore vers WordPress.** Une fois terminé, le site est republié automatiquement.
3. **Vérifier** : le site est visible à l'adresse indiquée dans *Settings › Pages*. Le fichier `data/media-missing.txt` liste les éventuels fichiers qui n'ont pas pu être récupérés.
4. **Brancher le domaine** : chez le registrar de `thequietadventure.com`, remplacer les enregistrements DNS :
   - quatre enregistrements `A` vers `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` ;
   - un enregistrement `CNAME` `www` vers `splintersteph.github.io`.
   Puis dans *Settings › Pages › Custom domain*, saisir `thequietadventure.com`, enregistrer, et cocher **Enforce HTTPS** quand GitHub le propose.
5. Les anciennes adresses des récits (`/2025/09/26/de-la-venetie-au-piemont/`) sont conservées à l'identique, et les anciennes pages de catégories redirigent vers les voyages : les liens existants continuent de fonctionner.

## Écrire un nouveau récit

Créer un fichier dans `content/posts/`, nommé `AAAA-MM-JJ-titre-du-recit.html` :

```html
<!--
{
  "title": "Le titre du récit",
  "date": "2025-10-12 18:00:00",
  "slug": "titre-du-recit",
  "url": "/2025/10/12/titre-du-recit/",
  "categories": ["france", "voyages-a-velo"],
  "cover": "/media/2025/10/photo-de-couverture.jpg",
  "description": "Une phrase pour Google et les réseaux sociaux.",
  "geo": [45.19, 5.72],
  "strava": [],
  "lang": "fr"
}
-->
<h4>Dimanche 12 octobre</h4>
<p>Le texte du récit…</p>
<div class="gallery g3"><img src="/media/2025/10/a.jpg" alt="…"><img src="/media/2025/10/b.jpg" alt="…"><img src="/media/2025/10/c.jpg" alt="…"></div>
<div class="strava" data-activity="12345678901"></div>
```

- Les photos vont dans `media/AAAA/MM/` (largeur conseillée : 1600 px).
- `geo` place le récit sur la carte (latitude, longitude).
- Une ligne `<div class="strava" data-activity="…">` affiche un encart « Trace du jour » vers l'activité Strava.
- Le récit est rangé automatiquement dans un voyage selon ses catégories et sa date (voir `data/trips.json`).

## Ajouter un voyage ou un livre

- Voyages : `data/trips.json` (titre, période, texte d'introduction en français et en anglais, photo, règles de rattachement des récits).
- Livres : `data/books.json`.
- Traces GPS d'un voyage : `data/traces/<nom>.json`, liste de `[départ, arrivée, polyline Strava]`.

## Prévisualiser sur son ordinateur

```
python3 tools/build.py --serve
```

puis ouvrir http://localhost:8000.

## Organisation

| Dossier | Contenu |
| --- | --- |
| `content/posts/` | les 147 récits importés de WordPress |
| `content/pages/` | la page « Qui sommes-nous » (FR et EN) |
| `data/` | voyages, livres, traces GPS, liste des médias |
| `assets/` | styles, script, photos de la page d'accueil, couvertures des livres |
| `media/` | photos et vidéos des récits |
| `tools/` | `build.py` (génération du site), `fetch_media.py`, `import_wp.py` |

## Traces Strava

Les traces affichées sur les récits et les cartes viennent de `data/strava/activities.json` (sorties vélo et randonnées, sans les 300 premiers et derniers mètres de chaque trace).

- Un récit qui contient `<div class="strava" data-activity="ID"></div>` affiche automatiquement la carte de cette sortie.
- Pour rattacher des sorties à un récit sans toucher au texte, ajouter les identifiants dans `data/strava/posts.json`, sous le nom du récit.
- Pour ajouter de nouvelles sorties : exporter la liste des activités Strava (avec les polylignes) en JSON, puis `python tools/strava_merge.py export.json`.

## Ce que le site sait faire en plus

- **Le globe de l'accueil** : les voyages se dessinent dans l'ordre, avec nos traces GPS (vélo, marche) et les liaisons racontées dans les récits (train, car, voiture, bateau, avion). Ces liaisons sont dans `data/routes.json`, voyage par voyage. Les mêmes liaisons apparaissent en pointillés sur la carte de chaque voyage.
- **Le récit au fil de la route** : sur un récit qui a des traces Strava, la carte, le profil d'altitude et la petite barre du haut suivent la lecture. Chaque intertitre daté (« Mardi 16 septembre ») est relié à la sortie Strava du même jour. Les altitudes sont dans `data/altitude/altitude.json` (une liste de 60 points par sortie) ; une sortie sans altitude s'affiche simplement sans profil.
- **Le passeport** (`/passeport/`) : un tampon par pays, calculé à partir des catégories des récits.
- **La recherche** : bouton loupe ou touche `/`, dans les deux langues.
- **Les aperçus de partage** : une image 1200 × 630 est générée pour chaque récit (`/og/…`), avec la photo, le tampon du voyage, la trace et les kilomètres. Pour construire plus vite sur son ordinateur : `python3 tools/build.py --no-og`.
- **Le mode nuit** suit le réglage de l'appareil, et le bouton lune/soleil le change.
- **Les photos** s'affichent d'abord floues (aperçu de quelques octets gardé dans `data/lqip.json`, complété automatiquement), puis nettes, et s'ouvrent dans une visionneuse qu'on fait défiler au doigt.
