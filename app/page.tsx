"use client";
import HeroSection from "@/components/home/HeroSection";
import PipelineSection from "@/components/home/PipelineSection";
import FeaturesGrid from "@/components/home/FeaturesGrid";
import LiveDemoSection from "@/components/home/LiveDemoSection";
import MetricsPreview from "@/components/home/MetricsPreview";
import FooterSection from "@/components/home/FooterSection";
import ParticlesCanvas from "@/components/home/ParticlesCanvas";
import DotNavigation from "@/components/layout/DotNavigation";


const sections = [
  { id: "hero", label: "Home" },
  { id: "pipeline", label: "Pipeline" },
  { id: "features", label: "Features" },
  { id: "demo", label: "Demo" },
  { id: "metrics", label: "Metrics" },
  { id: "cta", label: "Get Started" },
];

export default function HomePage() {
  return (
    <div className="relative">
      <ParticlesCanvas />
      <DotNavigation sections={sections} />
      <section id="hero"><HeroSection /></section>
      <section id="pipeline"><PipelineSection /></section>
      <section id="features"><FeaturesGrid /></section>
      <section id="demo"><LiveDemoSection /></section>
      <section id="metrics"><MetricsPreview /></section>
      <section id="cta"><FooterSection /></section>
    </div>
  );
}
