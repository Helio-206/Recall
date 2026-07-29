export type LandingLocale = "pt" | "en";

export const landingCopy = {
  pt: {
    navigation: {
      label: "Navegação principal",
      mobileLabel: "Navegação móvel",
      product: "Produto",
      flow: "Como funciona",
      study: "Experiência de estudo",
      signIn: "Entrar",
      openMenu: "Abrir navegação",
      closeMenu: "Fechar navegação",
      home: "Página inicial da Recall",
    },
    actions: {
      openDashboard: "Abrir painel",
      startLearning: "Começar a aprender",
      seeProduct: "Ver o produto",
      createAccount: "Criar conta",
    },
    language: {
      label: "Selecionar idioma",
      portuguese: "Português",
      english: "Inglês",
    },
    hero: {
      badge: "Criado para uma aprendizagem focada e contínua",
      title: "O seu sistema de aprendizagem",
      titleAccent: "para vídeos da internet.",
      description:
        "A Recall transforma vídeos dispersos em percursos de aprendizagem estruturados, com transcrições sincronizadas, progresso claro e um ponto certo para continuar.",
      dashboardAlt: "Painel da Recall com percursos de aprendizagem, progresso e atividade recente",
    },
    flow: {
      eyebrow: "Um ciclo de aprendizagem mais claro",
      title: "Do link ao percurso de aprendizagem.",
      description:
        "Sem configurações complexas. Adicione o conteúdo em que já confia e mantenha todo o contexto de aprendizagem à volta dele.",
      steps: [
        {
          title: "Adicione uma fonte",
          description:
            "Cole um vídeo ou playlist do YouTube. A Recall organiza os metadados automaticamente.",
        },
        {
          title: "Construa o seu percurso",
          description:
            "Mantenha as aulas organizadas em espaços focados, com progresso sempre visível.",
        },
        {
          title: "Estude com contexto",
          description:
            "Assista, leia a transcrição sincronizada, tome notas e continue exatamente onde parou.",
        },
      ],
    },
    study: {
      eyebrow: "Estude com contexto",
      title: "Vídeo e transcrição, sincronizados.",
      description:
        "Navegue pelo currículo, acompanhe a transcrição completa e retome a aula certa no momento certo.",
      desktopAlt: "Ambiente de estudo da Recall com vídeo, transcrição sincronizada e currículo",
      mobileAlt: "Ambiente de estudo da Recall num dispositivo móvel",
      benefits: ["Navegação por timestamps", "Progresso automático", "Continuidade curricular"],
    },
    closing: {
      eyebrow: "Um espaço de trabalho. Todas as aulas.",
      title: "Pare de acumular vídeos.",
      titleAccent: "Comece a construir conhecimento.",
    },
    footer: {
      description: "Aprendizagem estruturada a partir do conteúdo em que já confia.",
    },
  },
  en: {
    navigation: {
      label: "Main navigation",
      mobileLabel: "Mobile navigation",
      product: "Product",
      flow: "How it works",
      study: "Study experience",
      signIn: "Sign in",
      openMenu: "Open navigation",
      closeMenu: "Close navigation",
      home: "Recall home",
    },
    actions: {
      openDashboard: "Open dashboard",
      startLearning: "Start learning",
      seeProduct: "See the product",
      createAccount: "Create account",
    },
    language: {
      label: "Select language",
      portuguese: "Portuguese",
      english: "English",
    },
    hero: {
      badge: "Built for focused, continuous learning",
      title: "Your learning OS",
      titleAccent: "for internet video.",
      description:
        "Recall turns scattered videos into structured learning paths with synchronized transcripts, clear progress, and a place to continue.",
      dashboardAlt: "Recall dashboard showing learning spaces, progress, and recent activity",
    },
    flow: {
      eyebrow: "A clearer learning loop",
      title: "From link to learning path.",
      description:
        "No complex setup. Add the material you already trust and keep the learning context around it.",
      steps: [
        {
          title: "Add a source",
          description:
            "Paste a YouTube video or playlist. Recall organizes the metadata automatically.",
        },
        {
          title: "Build your path",
          description:
            "Keep lessons ordered inside focused spaces with progress that stays visible.",
        },
        {
          title: "Study with context",
          description:
            "Watch, read the synchronized transcript, take notes, and continue where you left off.",
        },
      ],
    },
    study: {
      eyebrow: "Study with context",
      title: "Video and transcript, in sync.",
      description:
        "Navigate the curriculum, follow the complete transcript, and resume the exact lesson that matters.",
      desktopAlt: "Recall study workspace with video, synchronized transcript, and curriculum",
      mobileAlt: "Recall study workspace on mobile",
      benefits: ["Timestamp navigation", "Automatic progress", "Curriculum continuity"],
    },
    closing: {
      eyebrow: "One workspace. Every lesson.",
      title: "Stop collecting videos.",
      titleAccent: "Start building knowledge.",
    },
    footer: {
      description: "Structured learning from the content you already trust.",
    },
  },
} as const;
