"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, ArrowRight } from "lucide-react";

export function SiteHeader() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const pathname = usePathname();

  // Track scroll state for subtle elevation/shadow adjustment
  useEffect(() => {
    function handleScroll() {
      setIsScrolled(window.scrollY > 12);
    }
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileMenuOpen]);

  // Close mobile menu on resize to desktop breakpoint
  useEffect(() => {
    function handleResize() {
      if (window.innerWidth >= 768 && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [mobileMenuOpen]);

  // Automatically close mobile menu on route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/how-it-works", label: "How It Works" },
    { href: "/check", label: "Check a Subscription" },
  ];

  const isLinkActive = (href: string) => {
    if (!pathname) return false;
    if (href === "/") {
      return pathname === "/";
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  const handleHomeClick = (e: React.MouseEvent) => {
    setMobileMenuOpen(false);
    if (pathname === "/") {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-[#141312]/20 backdrop-blur-[2px] z-40 md:hidden transition-opacity duration-200"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Floating Navbar Container */}
      <header className="sticky top-0 z-50 w-full pt-3 sm:pt-4 px-4 sm:px-6 pointer-events-none transition-all duration-200">
        <div className="max-w-5xl mx-auto pointer-events-auto">
          {/* Main Floating Pill */}
          <div
            className={`relative flex items-center justify-between h-14 sm:h-15 px-3.5 sm:px-4 md:px-5 rounded-full border bg-[#FAF9F7]/90 backdrop-blur-md transition-all duration-300 ease-out ${
              isScrolled
                ? "bg-[#FAF9F7]/95 border-[#DCD8CB] shadow-[0_8px_30px_-6px_rgba(20,19,18,0.08),0_2px_8px_-2px_rgba(20,19,18,0.04)]"
                : "border-[#E8E5DC] shadow-[0_4px_20px_-4px_rgba(20,19,18,0.05),0_1px_4px_-1px_rgba(20,19,18,0.03)]"
            } hover:shadow-[0_10px_32px_-6px_rgba(20,19,18,0.1),0_4px_12px_-2px_rgba(20,19,18,0.04)] hover:border-[#D6D1C9] motion-reduce:transition-none motion-reduce:hover:shadow-none`}
          >
            {/* Left: ExitLens Logo & Wordmark */}
            <div className="flex-1 flex items-center justify-start">
              <Link
                href="/"
                onClick={handleHomeClick}
                className="group flex items-center gap-2.5 text-[#191817] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2 rounded-full transition-opacity duration-200"
                aria-label="ExitLens homepage"
              >
                <div className="w-7 h-7 rounded-full bg-[#191817] text-white flex items-center justify-center transition-transform duration-200 group-hover:scale-105 motion-reduce:group-hover:scale-100 shadow-sm">
                  <span className="font-serif font-bold text-sm leading-none">E</span>
                </div>
                <span className="font-serif font-bold text-lg tracking-tight text-[#191817]">
                  ExitLens
                </span>
              </Link>
            </div>

            {/* Center: Navigation Links */}
            <nav
              className="hidden md:flex items-center justify-center gap-1.5 lg:gap-2 text-xs sm:text-sm"
              aria-label="Primary navigation"
            >
              {navLinks.map((link) => {
                const active = isLinkActive(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={(e) => {
                      if (link.href === "/" && pathname === "/") {
                        handleHomeClick(e);
                      }
                    }}
                    className={`relative inline-flex items-center gap-1.5 px-3 sm:px-3.5 py-1.5 rounded-full font-medium transition-all duration-200 ease-out motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2 ${
                      active
                        ? "text-[#191817] bg-[#F3F1EA] shadow-[0_1px_2px_rgba(20,19,18,0.04)] border border-[#E8E5DC]/80 font-semibold"
                        : "text-[#64615B] hover:text-[#191817] hover:bg-[#F3F1EA]/60 border border-transparent"
                    }`}
                    aria-current={active ? "page" : undefined}
                  >
                    {active && (
                      <span
                        className="w-1.5 h-1.5 rounded-full bg-[#191817] transition-all duration-200"
                        aria-hidden="true"
                      />
                    )}
                    <span>{link.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Right: Single Primary CTA */}
            <div className="flex-1 hidden md:flex items-center justify-end">
              <Link
                href="/check"
                className="group inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs sm:text-sm font-medium text-white bg-[#191817] hover:bg-[#2C2A28] active:bg-[#141312] rounded-full transition-all duration-200 ease-out shadow-[0_2px_8px_-2px_rgba(25,24,23,0.18)] hover:shadow-[0_4px_12px_-2px_rgba(25,24,23,0.25)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2 shrink-0 motion-reduce:transition-none"
              >
                <span>Start an Audit</span>
                <ArrowRight
                  className="w-3.5 h-3.5 transition-transform duration-200 ease-out group-hover:translate-x-1 motion-reduce:transform-none"
                  aria-hidden="true"
                />
              </Link>
            </div>

            {/* Mobile: Menu Toggle Button */}
            <div className="flex md:hidden items-center">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 text-[#191817] hover:bg-[#F3F1EA] active:bg-[#EAE7DD] rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-nav-menu"
                aria-label={mobileMenuOpen ? "Close menu" : "Open navigation menu"}
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5 transition-transform duration-200" aria-hidden="true" />
                ) : (
                  <Menu className="w-5 h-5 transition-transform duration-200" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          {/* Accessible Mobile Dropdown Menu */}
          {mobileMenuOpen && (
            <div
              id="mobile-nav-menu"
              className="md:hidden mt-2 rounded-2xl border border-[#E8E5DC] bg-[#FAF9F7]/98 backdrop-blur-lg shadow-[0_12px_32px_-6px_rgba(20,19,18,0.12),0_4px_12px_-2px_rgba(20,19,18,0.06)] p-3.5 space-y-3 transition-all duration-200 animate-in fade-in slide-in-from-top-2"
            >
              {/* Mobile Navigation Links */}
              <nav className="flex flex-col space-y-1" aria-label="Mobile navigation">
                {navLinks.map((link) => {
                  const active = isLinkActive(link.href);
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] ${
                        active
                          ? "bg-[#F3F1EA] text-[#191817] font-semibold border border-[#E8E5DC]/80 shadow-[0_1px_2px_rgba(20,19,18,0.04)]"
                          : "text-[#64615B] hover:text-[#191817] hover:bg-[#F3F1EA]/60 font-medium border border-transparent"
                      }`}
                      aria-current={active ? "page" : undefined}
                    >
                      <span>{link.label}</span>
                      {active && (
                        <span
                          className="w-1.5 h-1.5 rounded-full bg-[#191817]"
                          aria-hidden="true"
                        />
                      )}
                    </Link>
                  );
                })}
              </nav>

              {/* Mobile Primary CTA */}
              <div className="pt-1">
                <Link
                  href="/check"
                  onClick={() => setMobileMenuOpen(false)}
                  className="group flex items-center justify-center gap-1.5 w-full px-4 py-2.5 text-sm font-medium text-white bg-[#191817] hover:bg-[#2C2A28] active:bg-[#141312] rounded-xl transition-colors duration-200 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817]"
                >
                  <span>Start an Audit</span>
                  <ArrowRight
                    className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1 motion-reduce:transform-none"
                    aria-hidden="true"
                  />
                </Link>
              </div>

              {/* Supporting Clarification */}
              <div className="pt-2 border-t border-[#E8E5DC]">
                <p className="text-xs text-[#6B6762] text-center leading-relaxed">
                  Understand the cancellation journey. Keep the choice yours.
                </p>
              </div>
            </div>
          )}
        </div>
      </header>
    </>
  );
}

export default SiteHeader;
