# Instructor Console

Responsive web application for marksmanship instructors, range masters, and training evaluators.

## Technologies
- **Framework**: React 18 with TypeScript (Strict Mode)
- **Build Tool**: Vite
- **Styling**: Tailwind CSS (optimized for dark room range environments)
- **Internationalization**: i18next (English, Hindi, French)
- **Icons**: Lucide React

## Responsive Layout
Designed for both desktop monitors (multi-column command view) and ruggedized tablets (touch-friendly collapsible navigation).

## Placeholder Views
- **Dashboard**: High-level status monitors for Backend, Tracker, Unreal, Camera, Guns, Projector, and Licence.
- **Session Setup**: Lane trainee rosters and course selection.
- **Live Session**: Real-time optical reticle tracking and range safety controls.
- **Shot Analysis**: Mean Point of Impact (MPI) and shot dispersion clusters.
- **Replay**: Frame-by-frame 120 Hz pre-shot kinematic aim trace playback.
- **Trainees**: Trainee service records and historical scores.
- **Reports**: After-action qualification certificate exports.
- **Weapons**: RF weapon pairings and battery levels.
- **Target Editor**: Target geometry and scoring ring definitions.
- **Exercise Builder**: Marksmanship drill sequencer.
- **Video Scenario Editor**: Branching video scenario manager.
- **Calibration**: 4-point projector screen homography and weapon optical zeroing.
- **Settings**: Network ports and application options.
- **Login**: Instructor credentials authentication.

## Development & Execution

```powershell
# Install dependencies
npm install

# Start local dev server
npm run dev
```

Server defaults to: `http://127.0.0.1:5173`
