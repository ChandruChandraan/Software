import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      appTitle: "Firing Training Simulator",
      tagline: "Professional Marksmanship & Telemetry Suite",
      dashboard: "Dashboard",
      sessionSetup: "Session Setup",
      liveSession: "Live Session",
      shotAnalysis: "Shot Analysis",
      replay: "Replay",
      trainees: "Trainees",
      reports: "Reports",
      weapons: "Weapons",
      targetEditor: "Target Editor",
      exerciseBuilder: "Exercise Builder",
      videoScenarioEditor: "Video Scenarios",
      calibration: "Calibration",
      settings: "Settings",
      login: "Login",
      logout: "Logout",
      services: {
        backend: "Backend Service",
        tracker: "Optical Tracker",
        unreal: "Unreal Engine",
        camera: "High-Speed Camera",
        guns: "Weapons RF Link",
        projector: "Display Projector",
        licence: "Licence Status",
      },
      status: {
        online: "Online",
        offline: "Offline",
        degraded: "Degraded",
        connected: "Connected",
        active: "Active",
      }
    }
  },
  hi: {
    translation: {
      appTitle: "फायरिंग ट्रेनिंग सिम्युलेटर",
      tagline: "पेशेवर निशानेबाजी और टेलीमेट्री सुइट",
      dashboard: "डैशबोर्ड",
      sessionSetup: "सत्र सेटअप",
      liveSession: "लाइव सत्र",
      shotAnalysis: "शॉट विश्लेषण",
      replay: "रीप्ले",
      trainees: "प्रशिक्षु",
      reports: "रिपोर्ट",
      weapons: "हथियार",
      targetEditor: "लक्ष्य संपादक",
      exerciseBuilder: "अभ्यास निर्माता",
      videoScenarioEditor: "वीडियो परिदृश्य",
      calibration: "अंशांकन",
      settings: "सेटिंग्स",
      login: "लॉग इन",
      logout: "लॉग आउट",
      services: {
        backend: "बैकएंड सेवा",
        tracker: "ऑप्टिकल ट्रैकर",
        unreal: "अनरियल इंजन",
        camera: "हाई-स्पीड कैमरा",
        guns: "हथियार लिंक",
        projector: "प्रोजेक्टर",
        licence: "लाइसेंस स्थिति",
      },
      status: {
        online: "ऑनलाइन",
        offline: "ऑफ़लाइन",
        degraded: "अवरुद्ध",
        connected: "संबद्ध",
        active: "सक्रिय",
      }
    }
  },
  fr: {
    translation: {
      appTitle: "Simulateur de Tir d'Entraînement",
      tagline: "Suite Professionnelle de Tir et de Télémétrie",
      dashboard: "Tableau de Bord",
      sessionSetup: "Configuration",
      liveSession: "Session en Direct",
      shotAnalysis: "Analyse des Tirs",
      replay: "Relecture",
      trainees: "Stagiaires",
      reports: "Rapports",
      weapons: "Armes",
      targetEditor: "Éditeur de Cibles",
      exerciseBuilder: "Créateur d'Exercices",
      videoScenarioEditor: "Scénarios Vidéo",
      calibration: "Étalonnage",
      settings: "Paramètres",
      login: "Connexion",
      logout: "Déconnexion",
      services: {
        backend: "Service Backend",
        tracker: "Traqueur Optique",
        unreal: "Moteur Unreal",
        camera: "Caméra Haute Vitesse",
        guns: "Liaison RF Armes",
        projector: "Projecteur",
        licence: "Licence",
      },
      status: {
        online: "En Ligne",
        offline: "Hors Ligne",
        degraded: "Dégradé",
        connected: "Connecté",
        active: "Actif",
      }
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
