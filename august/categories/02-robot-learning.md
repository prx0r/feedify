# Robot Learning / Sim2Real / Embodiment

## Why We Picked These Accounts

The thesis: Physical embodiment is the ultimate bottleneck for AI. Robot data doesn't scale like internet data. The person/world interaction layer is where bits become atoms.

## Accounts

| Handle | Followers | Source Distance | August | Total | Why Picked |
|--------|-----------|----------------|--------|-------|------------|
| @JunjieYe9 | 330 | 0 (experimenter) | 0 | 11 | Reusable robot world models |
| @KostasPenn | 5.1K | 0 (experimenter) | 2 | 2 | VLA scaling critique |
| @TweetEdMiller | 3.6K | 2 (specialist) | 0 | 39 | Robot-data economics |
| @palm_alessio | 41 | 0 (experimenter) | 0 | 19 | Embodied-AI PhD |
| @f1she1 | 138 | 0 (experimenter) | 0 | 5 | UCSD Sim2Real PhD |
| @fei_fay | 128 | 0 (experimenter) | 0 | 20 | Safe/robust embodied-AI |
| @Jia_Fei_Yu | ~500 | 0 (experimenter) | 0 | 5 | Humanoid teleoperation |
| @MotonariKambara | ~1K | 0 (experimenter) | 0 | 22 | Toyota R&D robotics |
| @KyleStachowicz | ~1K | 0 (experimenter) | 0 | 25 | Berkeley/PI robot learning |
| @YuchenXiao5 | ~1K | 0 (experimenter) | 0 | 17 | Unitree embodied-AI |
| @songming_liu | ~500 | 0 (experimenter) | 0 | 17 | RDT2 generalizable policies |
| @ryancjulian | ~2K | 0 (experimenter) | 20 | 32 | NVIDIA GEAR, ex-DeepMind |
| @danfei_xu | ~2K | 0 (experimenter) | 6 | 30 | Robot learning and reasoning |
| @TimSong52005757 | ~500 | 0 (experimenter) | 0 | 2 | Robot perception-action |
| @LongLeRobot | ~1K | 0 (experimenter) | 0 | 27 | Composable robot intelligence |

## What We Hoped to Get

- Evidence that robot data is the bottleneck (not algorithms)
- Whether world models transfer across tasks
- Physical data collection costs and scaling limits
- Sim2real gap status

## What We Got

### @JunjieYe9 (0 August — last tweet Jun 19)
**Key finding**: AnchorDream accepted to ICRA2026 — one reusable world model across three robotic tasks
- VideoGPA accepted to ICML2026 — 3D consistency for video diffusion
- DUET — pretrain on human-human collab, fine-tune with few robot demos
- **Alpha**: World-model infrastructure becomes reusable capital vs task-specific policies

### @KostasPenn (2 August tweets)
**Key finding**: VLA systems ingest enormous teleoperation datasets yet ignore pretrained perception at inference
- Injects 3D perception-derived energy fields without policy retraining
- **Alpha**: "Everyone is scaling the wrong variable" — perception at inference time matters more than more training data

### @TweetEdMiller (0 August — last tweet Sep 8)
**Key finding**: Robot-specific data doesn't scale easily, but human egocentric data does
- Changes which data-collection infrastructure becomes valuable
- **Alpha**: Human data is the scalable path, not robot-specific collection

### @ryancjulian (20 August tweets)
**Key finding**: NVIDIA GEAR researcher — active in robot learning
- Ex-DeepMind, Everyday Robots background
- **Alpha**: Industry insider view on what's working in embodied AI

## Top Alpha from This Category

1. **World models transfer** — @JunjieYe9 shows one model across three tasks
2. **Perception at inference > more training data** — @KostasPenn's VLA critique
3. **Human data scales, robot data doesn't** — @TweetEdMiller's economic framing
4. **Physical embodiment is the real bottleneck** — everyone agrees, nobody has solved it
