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
