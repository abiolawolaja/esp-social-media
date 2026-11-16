# ESP carousel template

The house layout for EventSpacePro carousel posts: 1080×1350 (4:5) slides with a fixed frame
(logo top left, slide counter top right, navy footer with eventspacepro.com and the current call to action),
two-tone headlines (words in *asterisks* turn Brand Blue), and app screens in a browser-style frame.

To make a new carousel, copy a brief in `briefs/`, change the words and the screen file names,
put any new screens in `assets/screens/`, then run:

    python3 build.py briefs/<name>.json

Slides come out in `out/<id>/01.jpg …` plus `sheet.jpg` for review.

Rules
- The browser frame's address bar stays empty. Only add `app_url` to a slide when Abi says the app link can be shown.
- Crop every app screen so no client or project names, emails or avatars show.
- Only claim features that are visible and live in the app; check with Abi when unsure.
- Brand: Navy #021938, Brand Blue #0056A9, Blue tint #EEF2FB; Plus Jakarta Sans for headlines, Inter for body.
- Voice: talk to one person, lead with the outcome. Never use book, magic, effortless, seamless or users.

Layouts: `cover` (navy, pill + headline + screen), `feature` (kicker + headline + body + screen, chips, or callout), `cta` (navy, headline + button).
