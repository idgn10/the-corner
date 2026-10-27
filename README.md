[Español](README.es.md) · English

# The Corner · AI boxing analysis

A personal product prototype. Live app: https://thecorner-boxeo.streamlit.app/
(sample result without uploading anything: `?demo=1`).

You upload a 20-60 second shadowboxing video and, within about a minute, you get back your video with the
skeleton drawn on it, a card with your score from 0 to 100, your session second by second, and three
concrete tips for next time.

The idea comes from camera-and-AI padel analysis (pose estimation, "digital skeleton", player card and
virtual coach), applied to a sport where people almost always train alone.

## How it was built

Personal project. I own the product: I define the problem, the scope, what gets measured, how it is scored
and how it is validated. Claude Code writes the code following those decisions. The product and calibration
decisions are documented in [docs/DECISIONES.md](docs/DECISIONES.md) (in Spanish).

## Try the app

The app is published on Streamlit Community Cloud: https://thecorner-boxeo.streamlit.app/. It is a cost
decision: hosting is free while the prototype is being validated.

- To see it without uploading any video, open demo mode: https://thecorner-boxeo.streamlit.app/?demo=1
- If it hasn't been used for a while, the app goes to sleep. When you open it, a notice appears with a button to
  wake it up: press it and wait for it to load.
- The free server has little computing power, so the analysis takes longer than on a computer.
- It is a prototype under validation: the score is calibrated with a single person (see Known limitations).
- What happens to your video: while it is analyzed, it is written to a temporary folder on the server with a
  random name, which is deleted entirely when the analysis ends, whether it succeeds or fails. The video with the
  skeleton and the card stay only in your session's memory and are released when you press "Analizar otro vídeo"
  (analyze another video) or when the session closes. The only exception is a server crash in the middle of an
  analysis: the temporary folder may then remain until the server restarts.

---

## 1. The problem

In amateur boxing most technical training is shadowboxing and bag work with nobody watching.
The mistakes that cost the most in a fight (dropping your guard, letting the non-punching hand fall,
not extending the arm, being slow to recover) are exactly the ones you can't see in yourself. Today's options:

- Coach or training partner: expensive or not always available.
- Filming yourself and reviewing it: slow, and with no clear criteria for what to look at.
- Fitness apps with boxing: they count punches or calories; they don't correct technique.

## 2. User

An amateur or fitness-boxing athlete who trains alone several times a week, at home or at the gym, and
wants to improve technique between classes. They have a phone and 5 minutes.
What they need is not a biomechanics report: it's to **know what to fix tomorrow** and to be able to check
whether they are improving.

## 3. What it does

1. Upload your video from your phone (MP4 or iPhone MOV, as is) and choose your stance (orthodox or southpaw).
2. We analyze it: we detect your skeleton frame by frame, count your punches and measure your technique.
3. Improve with your card:
   - Total score from 0 to 100, jabs, crosses and punches per minute.
   - Your plan for the next session: 3 tips ordered by how much each one costs you, each with your own data.
   - Your video with the skeleton, a label on every punch (jab, cross, hook, uppercut, dodge), a counter
     of straight punches, curved punches and dodges, and a guard indicator (green/red when the score measures it;
     grey during punches, while getting into position and at the end).
   - Your session, second by second: a chart with every punch of each hand and the moments with the guard down.
   - Moments to review: the longest stretches with the guard down; one click and the video jumps to that second.
   - Detail of each metric with a plain-language "How is it calculated?".

## 4. Scope (MoSCoW)

| Priority | What | Status |
|---|---|---|
| Must | Pose extraction, video with skeleton, per-hand punch detection, metrics, scoring, CLI and local app | Done |
| Should | Polished card, rule-based tips, deployment on Streamlit Community Cloud | Done (app published on Streamlit Community Cloud) |
| Could | Tips written with the Claude API, progress across sessions | Set aside for now (don't use generative AI where a rule is enough) |
| Beta | Detect hooks, uppercuts and dodges (they don't score; they stop counting as a straight punch and as a low guard) | Being tested, calibrated with a single boxer |
| Won't (for now) | Scoring curved punches and dodges, several people in frame, real time | Out of scope |

Beyond the initial plan: session chart, moments to review with a jump to the video, and a demo mode.

## 5. How it works

```
video (MP4/MOV) ─► pose (MediaPipe, 33 points/frame) ─► smoothing ─► punches ─► metrics ─► scores ─► tips
                                                                          └──► annotated video (H.264)
```

- Pose: MediaPipe Pose Landmarker in video mode, on the video downscaled to 720p at most.
  Points with visibility < 0.5 are ignored and the signal is smoothed with a 0.1 s moving median.
- Scale: every distance is measured in "shoulder widths" so it doesn't depend on how close the camera is.
- Punches: detected from the wrist: the moment it is furthest from the shoulder, reached by moving
  away quickly (increase in reach + speed peak). The elbow only acts as a filter: it must exceed 125°.
  If both hands "punch" at the same time (less than 0.15 s apart), only the one that goes furthest counts.
- Active segment: guard and rhythm are measured from 1 s before the first punch to 1 s after the
  last one, so that stepping into frame or getting ready doesn't count. Lowering your arms at the end doesn't
  count as a low guard either.
- Tips: rule-based, no generative AI: fast, free, explainable and always with the real figure.

Stack: Python 3.11 · MediaPipe · OpenCV · NumPy/pandas · Streamlit + Altair · imageio-ffmpeg.

## 6. Metrics and scoring

Each metric becomes a score from 0 to 100 through a straight line between a "bad" threshold (0) and a
"good" one (100). The total score is the weighted average. Everything can be tuned in [`config.yaml`](config.yaml) without touching code.
Full explanation, with a step-by-step example: [docs/SCORING.md](docs/SCORING.md) (in Spanish).

| Metric | What it measures | 0 points | 100 points | Weight |
|---|---|---|---|---|
| Guard | % of time between punches with both hands up | ≤ 40% | ≥ 90% | 25 |
| Opposite hand up | % of punches in which the other hand protects the face | ≤ 40% | ≥ 90% | 20 |
| Extension | % of punches with the elbow at ≥ 160° at the peak | ≤ 30% | ≥ 80% | 20 |
| Return to guard | Average seconds from the peak until back in guard (hand up and elbow < 90°) | ≥ 0.8 s | ≤ 0.4 s | 15 |
| Volume and rhythm | Punches per minute in the active segment | ≤ 20 | ≥ 70 | 10 |
| ~~Stance~~ | Foot separation and bent knees | - | - | 0 (see limitations) |

Hand "up": the wrist is less than 0.8 shoulder widths from the nose and above the elbow.

Tips: the 3 metrics that subtract the most from the score are chosen, `(100 − score) × weight`. With a score ≥ 85
the tip is one of reinforcement; below that, it is a correction and always comes with the figure (e.g. *"You drop your
left hand in 54% of your crosses: keep it glued to your chin while you punch with the other."*).

## 7. Validation and calibration decisions

I recorded 5 clips with an iPhone (almost side-on, 60 fps), each designed as a **test case**:
if the system doesn't lower the score on the right metric, something is wrong.

| Clip | What I did | Punches detected (left / right) | Score (v2) |
|---|---|---|---|
| Jabs | Jabs only | 10 / 0 | 92 |
| Crosses | Crosses only | 0 / 10 | 90 |
| 1-2 good | Combinations with good technique | 6 / 6 | 94 |
| 1-2 lazy | The same combinations, with deliberately worse technique | 15 / 13 | 72 |
| Free shadowboxing | Shadowboxing with movement, curved punches and dodges | 22 / 9 straight punches + 25 curved (13 hooks and 12 uppercuts) and 11 dodges (beta) | 82 |

All counts match the real punches. The "lazy" 1-2 loses 22 points against the good one, and it loses them
where it should: guard (100 → 65), opposite hand (87 → 70) and extension (100 → 69).

The scores are from scoring version v2 (curved punches and dodges in beta). They are only comparable between analyses
with the same version: with v1, free shadowboxing scored 57 (see `docs/DECISIONES.md`, point 17; in Spanish).

Decisions made with the data:

1. Wrist-based detection, minimum elbow of 125° (the initial plan asked for going from 110° to 150°).
   With the initial criterion a short punch did not count as a punch: the "not extended" clip would have
   had fewer punches instead of worse extension. Now a short punch counts and lowers the extension score.
2. Simultaneous-punch filter. When rotating the torso on a jab, the back hand moves just enough
   to look like a punch. If both hands "punch" less than 0.15 s apart, only the one that goes furthest counts.
3. Active segment. The first 10 s of the jabs clip were stepping into frame and getting ready: they lowered the
   guard (44 points) and the rhythm for no reason.
4. Stance with weight 0. Filming side-on, one foot hides the other and the ankles appear "together" in the
   image (18-31 px against 80 px of shoulders). Measuring it gave 0% in every clip: it isn't bad technique,
   it's that the camera can't see it.
5. Guard rule: elbow instead of shoulders. The initial rule ("wrist above the shoulder line")
   punished good technique: when tucking the chin or ducking to dodge, the hand is at the face
   but below the shoulders. I compared two alternatives on the 5 clips:

   | Clip | Shoulders (with 0.15 margin) | Elbow (nose < 0.8) |
   |---|---|---|
   | 1-2 good | 90 | 94 |
   | 1-2 lazy | 59 | 71 |
   | Shadowboxing (guard score) | 0 | 14 |

   These figures are from the time of the decision; with the current rules the shadowboxing guard score is 16.

   I chose the elbow rule even though it separates good from lazy a little less (23 points against 31). Checking
   frames of shadowboxing between punches, the shoulder rule marked "guard down" when the boxer was ducking with
   hands at the face, and gave 0 in guard to a shadowboxing clip where the hands are up almost half
   of the time. The elbow rule doesn't depend on body lean, which changes as soon as the user moves.
6. Curved punches are not filtered by raising the minimum elbow to 140°. That filtered some hooks, but also
   short straight punches from the "lazy" clip, which must count and be penalized. Instead, curved punches are detected
   separately (beta, see below) and only then stop counting as straight punches.
7. Return to guard with the arm tucked. Side-on, the extended jab fist ends up in the image
   in front of the face and the guard rule counted it as "up": returns of 0.0 s came out, which are impossible.
   Now the hand has to be up with the elbow below 90°, and before the next punch.
   In shadowboxing, returns in under 0.1 s drop from 17 to 3; the total scores don't change.

## 8. Known limitations

- Calibrated with a single person and 5 clips. It still has to be tested with other bodies, levels and phones.
- It needs a specific way of recording: fixed camera, full body, side-on or at a diagonal, and only one person in
  frame. Other camera angles would need recalibration; from the front it gives no score.
- Hooks, uppercuts and dodges are detected in test mode and don't count toward the score yet.
- It doesn't assess foot position: filming side-on, one foot hides the other.
- Results can vary slightly: with videos below 50 fps the score is marked as indicative, and the published app
  can count 1-2 punches differently from the local analysis.

Details of each limitation in [docs/DECISIONES.md](docs/DECISIONES.md#limitaciones-en-detalle) (in Spanish).

## 9. Next steps

1. Validation pilot with a local boxing gym (in preparation) to measure accuracy with other boxers.
2. Validate with 5-10 real users (other bodies, levels and camera angles) and recalibrate thresholds.
3. Progress across sessions: save each analysis and show the trend of the score and of each metric.
   It's what turns a one-off analysis into a habit.
4. Measurable stance: ask for a diagonal camera angle or estimate depth (MediaPipe 3D pose).
5. Take curved punches and dodges out of beta: validate them with other boxers and decide whether they score.
6. Guided rounds: "3 minutes of jab-cross" with goals, and compare the session with the previous one.
7. AI-written tips only if user testing shows the rules fall short.

---

## Installation and usage

Requires Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_model.py   # downloads the pose model into models/ (the app also does it on its own)
```

App:

```bash
streamlit run app.py
```

It opens at http://localhost:8501. To show a sample without uploading anything: http://localhost:8501/?demo=1
(the sample is prepared with `python scripts/make_demo.py outputs/<clip>`).

Terminal:

```bash
python scripts/analyze.py data/my_video.mov [--stance southpaw]
```

It generates in `outputs/my_video/`: `annotated.mp4` (H.264), `metrics.json` (metrics, scores, tips,
punches and timeline) and `landmarks.csv` (body points per frame).

How to record (the same text across the whole app, in `boxeo/recording.py`): phone in portrait and fixed, at 1.2 m
above the floor and level, with the rear camera; about 2 m away, in guard facing the phone and turning a little until it sits
between your forehead and your front shoulder (always punching toward where you look); full body with a hand's width of
margin above your arms and below your feet; a 5-second test that you record, watch and delete
before recording for real (face and both fists in view, nothing outside the image); free shadowboxing standing in place, no bag, no gloves and no wraps;
20 to 60 s at 60 frames per second; only one person in the image, with good light and no mirrors behind.

Deployment: see [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md) (in Spanish).

## Structure

```
app.py                 Streamlit interface
config.yaml            thresholds and weights (editable without touching code)
boxeo/
  pose.py              video -> body points per frame, smoothing
  metrics.py           angles, guard, stance, active segment, timeline
  punches.py           punch detection
  scoring.py           scores 0-100 and weighted total
  tips.py              rule-based tips
  render.py            annotated video in H.264
  card.py, charts.py   visual card and session chart
  pipeline.py          everything together (used by the app and the CLI)
scripts/               analyze.py, download_model.py, make_demo.py
demo/                  pre-analyzed sample for demo mode (metrics.json and annotated.mp4,
                       the only video in git)
docs/                  plan, roadmap, decisions and deployment (in Spanish)
```
