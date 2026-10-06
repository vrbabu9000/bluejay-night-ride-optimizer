# Prompt for the three-approaches figure (for other image generators)

The version we built is `FourSight_three_approaches.png`, drawn by `docs/technical/figures/build_gradient_figure.py`. Its paths are true gradient flows of the landscape it draws; a generated image will only look like one.

**Tips**
- Most image generators garble long text. Generate the scene with no text, then add the labels (listed at the end) in Keynote, PowerPoint or Figma.
- For the professor, attach his photo as a reference image if the tool allows it.
- Ask for portrait 4:5, 1800 × 2250 or larger.

---

## Prompt

A portrait (4:5) flat-cartoon illustration with thick dark outlines and a dark starry night-sky background.

The scene is a **glowing topographic landscape seen from above**, drawn as contour lines. Low ground is dark navy; high ground glows neon green, like light coming from inside the hills. Three green hilltops sit in the upper half of the image: one at the top centre, one on the right (lower), and one on the upper left. The upper-left hilltop is almost completely hidden under a soft, pale grey fog bank.

- **Bottom left (the abandoned start).** A grey dashed path starts at a small dot and climbs a short way toward a faint, ghostly dashed hill. It stops short at a red X. A small swirling green portal sits at the X, and a dotted green arc leads from it to a larger swirling green portal at the bottom centre: a restart.
- **The step.** From that portal, one bold white arrow climbs diagonally up to a small white dot, the fork, in the middle of the image.
- **Three paths climb from the fork,** each a curving line with evenly spaced dots, like optimizer iterates:
  1. a **yellow** path curving up to the **top-centre hilltop** (ending in a swirling green portal);
  2. a **blue** dash-dot path curving right to the **right hilltop** (ending in a smaller portal);
  3. a **pink** dotted path curving up-left into the **fog**, where three pink question marks float.
- **On the yellow path:** a royal-blue Ford Transit-style shuttle van, nose up, flying like a rocket. It has orange rear fins, a grey rocket nozzle with an orange and yellow flame, and a little smoke. The side reads "BLUE JAY SHUTTLE" and "962" in white, and four smiling students look out of the side windows.
- **Left side, below the fog:** a friendly older professor, matching the reference photo (short grey hair, full white beard and moustache, clear safety glasses with a black top bar, maroon shirt, brown tweed jacket). He holds up a glowing lantern whose soft yellow beam shines into the fog.
- **Top of the image:** a dark rounded legend panel, left empty for text, with a small horizontal colour bar on its right running from dark navy to bright green.

Mood: clear, clever, warm, uncluttered, with lots of negative space. The three paths must be easy to tell apart at a glance. No photorealism, no 3D render, no extra characters, no watermark, no logos.

---

## Labels to add afterwards (exact text)

| Where | Text |
|---|---|
| Legend header | Blue Jay Night Ride · Team FourSight |
| Legend rows | Approach 1 · Simulation + dispatch<br>Approach 2 · Events, zones and traffic<br>Approach 3 · What's in plain sight that we don't see<br>Initial scope (abandoned) |
| Colour bar ends | non-defensible (left) · defensible (right) |
| Start dot | 15 Sep · initial plan: replay April trip by trip |
| Red X | trip-level data never came |
| Bottom portal | 29 Sep · restart on aggregate data |
| White arrow | one step: charts digitized, data mined |
| Fork | 1 Oct |
| Paths | badges with titles: 1 Simulation + dispatch · 2 Events, zones and traffic · 3 a cartoon speech bubble "What's in plain sight that we don't see?" |
| White arrow (beside) | ∇D, with a dashed horizontal and an arc showing the step's angle (65°) |
| Under the professor | Prof. AJK |
