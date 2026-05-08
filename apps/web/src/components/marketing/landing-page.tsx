"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, CirclePlay, Search, Sparkles, Waypoints } from "lucide-react";

import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { label: "Produto", href: "#product" },
  { label: "Estrutura", href: "#structure" },
  { label: "Começar", href: "#start" },
] as const;

const CAPABILITY_CARDS = [
  {
    title: "Guardar",
    body: "Vídeos, playlists e canais entram no espaço certo em vez de se perderem em listas soltas.",
    image:
      "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
    alt: "Pessoa a trabalhar com portátil e bloco de notas",
  },
  {
    title: "Pesquisar",
    body: "Transcript, notas e sumários deixam de ser ruído e passam a recuperar o ponto exacto de uma explicação.",
    image:
      "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1200&q=80",
    alt: "Setup de trabalho com monitor e teclado em ambiente escuro",
  },
  {
    title: "Organizar",
    body: "O conteúdo passa a formar um percurso de estudo em vez de um arquivo que nunca mais é revisto.",
    image:
      "https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=1200&q=80",
    alt: "Pessoa em reunião de produto a analisar informação num ecrã",
  },
] as const;

const PROOF_ITEMS = [
  {
    title: "Spaces com contexto",
    body: "Cada captura mantém o tema, a intenção e o lugar onde volta a ser útil.",
  },
  {
    title: "Busca que recupera memória",
    body: "Encontrar a explicação certa deixa de depender de voltar a ver uma aula inteira.",
  },
  {
    title: "Percurso com continuidade",
    body: "O objectivo não é guardar mais. É aprender melhor ao longo do tempo.",
  },
] as const;

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#07080d] text-foreground">
      <div className="mx-auto max-w-7xl px-4 pb-16 pt-5 sm:px-6 lg:px-8 lg:pb-24 lg:pt-6">
        <header className="flex items-center justify-between gap-4 rounded-full border border-white/10 bg-[#090b12]/88 px-4 py-3 backdrop-blur-xl sm:px-6">
          <Logo />

          <nav className="hidden items-center gap-7 text-sm text-white/64 lg:flex">
            {NAV_ITEMS.map((item) => (
              <a key={item.label} href={item.href} className="transition-colors hover:text-white">
                {item.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild className="text-white/68 hover:bg-white/[0.06] hover:text-white">
              <Link href="/login">Entrar</Link>
            </Button>
            <Button asChild className="rounded-full bg-[linear-gradient(135deg,#B97AFF,#6B44F2_48%,#2F6BFF)] px-5 text-white hover:opacity-95">
              <Link href="/register">
                Criar conta
                <ArrowRight />
              </Link>
            </Button>
          </div>
        </header>

        <main className="pt-10 lg:pt-14">
          <section className="grid gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-center">
            <Reveal className="max-w-2xl">
              <p className="text-sm uppercase tracking-[0.22em] text-violet/80">Aprendizagem online com estrutura</p>
              <h1 className="mt-5 font-heading text-5xl font-semibold leading-[0.95] tracking-[-0.06em] text-white sm:text-6xl xl:text-[5.2rem]">
                O teu conteúdo não precisa morrer em separadores guardados.
              </h1>
              <p className="mt-6 max-w-xl text-base leading-8 text-white/60 sm:text-lg">
                Recall organiza o que aprendes na internet com contexto, pesquisa e continuidade. Menos backlog. Mais memória útil.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button asChild size="lg" className="rounded-full bg-[linear-gradient(135deg,#B97AFF,#6B44F2_48%,#2F6BFF)] px-7 text-white hover:opacity-95">
                  <Link href="/register">
                    Criar conta
                    <ArrowRight />
                  </Link>
                </Button>
                <Button asChild variant="ghost" size="lg" className="rounded-full px-2 text-white/62 hover:bg-transparent hover:text-white">
                  <Link href="/login">Entrar</Link>
                </Button>
              </div>
            </Reveal>

            <Reveal delay={0.08}>
              <aside className="grid gap-4">
                <div className="overflow-hidden rounded-[30px] border border-white/10 bg-[linear-gradient(180deg,rgba(17,19,31,0.96),rgba(8,9,15,0.98))] shadow-[0_30px_90px_rgba(0,0,0,0.34)]">
                  <div className="min-h-[360px] bg-[linear-gradient(180deg,rgba(8,9,15,0.14),rgba(8,9,15,0.74)),url(https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1400&q=80)] bg-cover bg-center p-6 lg:p-7">
                    <div className="max-w-sm rounded-[24px] border border-white/10 bg-[#090b12]/82 p-5 backdrop-blur-xl">
                      <p className="text-sm uppercase tracking-[0.2em] text-white/40">Vídeo do produto</p>
                      <h2 className="mt-3 font-heading text-2xl font-semibold leading-tight tracking-[-0.04em] text-white">
                        Reserva este espaço para a tua gravação real.
                      </h2>
                      <p className="mt-3 text-sm leading-7 text-white/58">
                        Sem demo genérica. Sem board glass. Quando gravares, este bloco recebe o teu walkthrough.
                      </p>
                      <div className="mt-6 flex items-center gap-3 text-sm text-white/68">
                        <span className="grid size-11 place-items-center rounded-full border border-white/10 bg-[linear-gradient(135deg,rgba(185,122,255,0.22),rgba(47,107,255,0.22))] text-white">
                          <CirclePlay className="size-5" />
                        </span>
                        Placeholder pronto para o teu vídeo
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    ["12", "espaços activos"],
                    ["148", "aulas guardadas"],
                    ["84%", "foco no percurso"],
                  ].map(([value, label]) => (
                    <div key={label} className="rounded-[24px] border border-white/10 bg-[#0b0d14] p-4">
                      <p className="font-heading text-3xl font-semibold tracking-[-0.05em] text-white">{value}</p>
                      <p className="mt-2 text-sm text-white/48">{label}</p>
                    </div>
                  ))}
                </div>
              </aside>
            </Reveal>
          </section>

          <section id="product" className="mt-20 grid gap-6 lg:grid-cols-[0.88fr_1.12fr] lg:items-start">
            <Reveal className="max-w-2xl">
              <p className="text-sm uppercase tracking-[0.22em] text-white/38">Quem é o Recall</p>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight tracking-[-0.05em] text-white sm:text-5xl">
                Um workspace para quem aprende da internet com intenção séria.
              </h2>
              <div className="mt-6 space-y-5 text-base leading-8 text-white/58">
                <p>
                  Recall nasce para transformar conteúdo disperso em estudo contínuo. Em vez de acumular vídeos guardados, a plataforma ajuda-te a dar contexto, reencontrar explicações e construir um percurso claro.
                </p>
                <p>
                  Para nós, aprender melhor não é consumir mais. É voltar rapidamente ao que interessa, com estrutura, memória e continuidade entre uma sessão e a seguinte.
                </p>
                <p>
                  O produto junta interface, pesquisa e organização num único sistema. Menos ruído. Mais clareza operacional para quem estuda a sério.
                </p>
              </div>
            </Reveal>

            <Reveal delay={0.08}>
              <div className="grid gap-4 lg:grid-cols-[0.82fr_1.18fr]">
                <div className="rounded-[30px] border border-violet/20 bg-[linear-gradient(180deg,rgba(16,14,26,0.96),rgba(10,10,17,0.98))] p-6 shadow-[0_24px_70px_rgba(0,0,0,0.28)]">
                  <Logo />
                  <p className="mt-6 text-sm uppercase tracking-[0.22em] text-violet/80">Your second brain for online learning</p>
                  <div className="mt-6 rounded-[22px] border border-white/10 bg-[#0c0f18] p-5">
                    <p className="text-sm leading-7 text-white/56">
                      Produto, pesquisa e progressão alinhados para que cada aula continue útil depois de ser guardada.
                    </p>
                  </div>
                </div>

                <article className="overflow-hidden rounded-[30px] border border-white/10 bg-[#0b0d14] shadow-[0_24px_70px_rgba(0,0,0,0.28)]">
                  <div
                    role="img"
                    aria-label="Painel de trabalho com ambiente técnico"
                    className="min-h-[340px] bg-[linear-gradient(180deg,rgba(7,8,13,0.08),rgba(7,8,13,0.62)),url(https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1400&q=80)] bg-cover bg-center"
                  />
                  <div className="p-6">
                    <p className="text-sm leading-7 text-white/56">
                      Uma assinatura visual mais editorial, mais humana e menos “feito por IA”, seguindo a lógica do YetuCoders mas com a paleta azul-violeta do Recall.
                    </p>
                  </div>
                </article>
              </div>
            </Reveal>
          </section>

          <section className="mt-20">
            <Reveal className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.22em] text-white/38">O que faz</p>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight tracking-[-0.05em] text-white sm:text-5xl">
                Actua onde contexto, busca e organização mudam a forma como estudas.
              </h2>
            </Reveal>

            <div className="mt-8 grid gap-4 lg:grid-cols-3">
              {CAPABILITY_CARDS.map((item, index) => (
                <Reveal key={item.title} delay={0.05 * index}>
                  <article className="overflow-hidden rounded-[28px] border border-white/10 bg-[#0b0d14] shadow-[0_24px_60px_rgba(0,0,0,0.24)]">
                    <div
                      role="img"
                      aria-label={item.alt}
                      className="min-h-[220px] bg-cover bg-center"
                      style={{
                        backgroundImage: `linear-gradient(180deg, rgba(7,8,13,0.10), rgba(7,8,13,0.58)), url(${item.image})`,
                      }}
                    />
                    <div className="p-6">
                      <h3 className="font-heading text-2xl font-semibold text-white">{item.title}</h3>
                      <p className="mt-3 text-sm leading-7 text-white/58">{item.body}</p>
                    </div>
                  </article>
                </Reveal>
              ))}
            </div>
          </section>

          <section id="structure" className="mt-20 grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <Reveal>
              <figure className="overflow-hidden rounded-[30px] border border-white/10 bg-[#0b0d14] shadow-[0_26px_80px_rgba(0,0,0,0.28)]">
                <div
                  role="img"
                  aria-label="Infraestrutura tecnológica em ambiente escuro"
                  className="min-h-[360px] bg-[linear-gradient(180deg,rgba(7,8,13,0.10),rgba(7,8,13,0.60)),url(https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=1400&q=80)] bg-cover bg-center"
                />
              </figure>
            </Reveal>

            <Reveal delay={0.08}>
              <p className="text-sm uppercase tracking-[0.22em] text-white/38">Estrutura & Continuidade</p>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight tracking-[-0.05em] text-white sm:text-5xl">
                Construído para dar continuidade ao que aprendes, não só para o guardar.
              </h2>
              <p className="mt-5 text-base leading-8 text-white/58">
                Da captura à pesquisa, o Recall trata memória, organização e consistência como parte do produto. Não como detalhe tardio.
              </p>

              <div className="mt-8 grid gap-3">
                {PROOF_ITEMS.map((item, index) => {
                  const Icon = index === 0 ? Sparkles : index === 1 ? Search : Waypoints;

                  return (
                    <div key={item.title} className="rounded-[24px] border border-white/10 bg-[#0b0d14] p-5">
                      <div className="flex items-start gap-4">
                        <span className="grid size-11 shrink-0 place-items-center rounded-2xl border border-violet/20 bg-[linear-gradient(135deg,rgba(185,122,255,0.16),rgba(47,107,255,0.16))] text-violet">
                          <Icon className="size-5" />
                        </span>
                        <div>
                          <h3 className="font-heading text-xl font-semibold text-white">{item.title}</h3>
                          <p className="mt-2 text-sm leading-7 text-white/56">{item.body}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Reveal>
          </section>

          <Reveal className="mt-20" delay={0.1}>
            <section
              id="start"
              className="rounded-[30px] border border-white/10 bg-[linear-gradient(180deg,rgba(13,14,24,0.96),rgba(7,8,13,0.98))] p-7 shadow-[0_30px_100px_rgba(0,0,0,0.3)] lg:p-10"
            >
              <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
                <div className="max-w-3xl">
                  <p className="text-sm uppercase tracking-[0.22em] text-white/38">Começar</p>
                  <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight tracking-[-0.05em] text-white sm:text-5xl">
                    Se a ideia é aprender melhor da internet, o Recall já pode começar daqui.
                  </h2>
                  <p className="mt-4 text-base leading-8 text-white/58">
                    A próxima etapa natural é trocar o placeholder pela tua gravação e ajustar as imagens para o teu gosto final.
                  </p>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button asChild size="lg" className="rounded-full bg-[linear-gradient(135deg,#B97AFF,#6B44F2_48%,#2F6BFF)] px-7 text-white hover:opacity-95">
                    <Link href="/register">
                      Criar conta
                      <ArrowRight />
                    </Link>
                  </Button>
                  <Button asChild variant="ghost" size="lg" className="rounded-full px-2 text-white/64 hover:bg-transparent hover:text-white">
                    <Link href="/login">Entrar</Link>
                  </Button>
                </div>
              </div>
            </section>
          </Reveal>
        </main>

        <footer className="mt-16 flex flex-col gap-6 border-t border-white/10 pt-8 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Logo />
            <p className="mt-3 max-w-xl text-sm leading-7 text-white/48">
              Recall é um workspace de aprendizagem para quem quer mais do que links guardados e memória vaga.
            </p>
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-white/50">
            <Link href="/login" className="transition-colors hover:text-white">Entrar</Link>
            <Link href="/register" className="transition-colors hover:text-white">Criar conta</Link>
            <Link href="/dashboard" className="transition-colors hover:text-white">Dashboard</Link>
          </div>
        </footer>
      </div>
    </div>
  );
}

function Reveal({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={prefersReducedMotion ? false : { opacity: 0, y: 28 }}
      whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.18 }}
      transition={{ duration: 0.75, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}