import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import {
  DashboardPage,
  LoginPage,
  SessionSetupPage,
  LiveSessionPage,
  ShotAnalysisPage,
  ReplayPage,
  TraineesPage,
  ReportsPage,
  WeaponsPage,
  TargetEditorPage,
  ExerciseBuilderPage,
  VideoScenarioEditorPage,
  CalibrationPage,
  SettingsPage,
} from './pages';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="session-setup" element={<SessionSetupPage />} />
          <Route path="live-session" element={<LiveSessionPage />} />
          <Route path="shot-analysis" element={<ShotAnalysisPage />} />
          <Route path="replay" element={<ReplayPage />} />
          <Route path="trainees" element={<TraineesPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="weapons" element={<WeaponsPage />} />
          <Route path="target-editor" element={<TargetEditorPage />} />
          <Route path="exercise-builder" element={<ExerciseBuilderPage />} />
          <Route path="video-scenarios" element={<VideoScenarioEditorPage />} />
          <Route path="calibration" element={<CalibrationPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
