"use client";

import React, { useState, useRef, useEffect, useId } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Check,
  ChevronDown,
  AlertCircle,
  ArrowRight,
  Loader2,
  Lock,
} from "lucide-react";
import { createRun, ApiClientError } from "@/lib/api";

const COMMON_SERVICES = [
  "StreamFlix India (Demo Site)",
  "Netflix",
  "Amazon Prime",
  "Disney+ Hotstar / JioCinema",
  "Spotify",
  "YouTube Premium",
  "Adobe Creative Cloud",
  "Times Prime",
  "Zee5",
  "SonyLIV",
  "Apple One",
  "Audible",
  "Microsoft 365",
  "Grammarly",
];

export function CheckFrictionForm() {
  const router = useRouter();

  // Form State
  const [service, setService] = useState("");
  const [startUrl, setStartUrl] = useState("");
  const [permissionConfirmed, setPermissionConfirmed] = useState(false);
  const [accountConfirmed, setAccountConfirmed] = useState(false);

  // Combobox State
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const comboboxRef = useRef<HTMLDivElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();

  // Submission & Validation State
  const [urlError, setUrlError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Filtered services
  const filteredServices = COMMON_SERVICES.filter((s) =>
    s.toLowerCase().includes(searchTerm.toLowerCase().trim())
  );

  // Close combobox when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (comboboxRef.current && !comboboxRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Validate URL on change
  function handleUrlChange(val: string) {
    setStartUrl(val);
    const trimmed = val.trim();
    if (!trimmed) {
      setUrlError(null);
      return;
    }
    try {
      const parsed = new URL(trimmed);
      if (parsed.protocol !== "https:") {
        setUrlError("Starting URL must use HTTPS (e.g., https://example.com/account).");
      } else {
        setUrlError(null);
      }
    } catch {
      setUrlError("Please enter a valid, complete URL (e.g. https://service.com/account).");
    }
  }

  // Keyboard navigation for combobox
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!isOpen) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightedIndex((prev) =>
        prev < filteredServices.length - 1 ? prev + 1 : 0
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightedIndex((prev) =>
        prev > 0 ? prev - 1 : filteredServices.length - 1
      );
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < filteredServices.length) {
        selectService(filteredServices[highlightedIndex]);
      } else if (searchTerm.trim()) {
        selectService(searchTerm.trim());
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
      setHighlightedIndex(-1);
    }
  }

  function selectService(name: string) {
    setService(name);
    setSearchTerm(name);
    setIsOpen(false);
    setHighlightedIndex(-1);
  }

  // Form Submission
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const chosenService = service.trim() || searchTerm.trim();
    if (!chosenService) {
      setSubmitError("Please specify or select a subscription service to audit.");
      inputRef.current?.focus();
      return;
    }

    if (urlError) {
      setSubmitError("Please correct the starting URL before proceeding.");
      return;
    }

    if (!permissionConfirmed || !accountConfirmed) {
      setSubmitError("Both safety & compliance confirmations are required to proceed.");
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await createRun({
        service: chosenService,
        start_url: startUrl.trim() || undefined,
        human_approved: true,
        test_account_confirmed: true,
      });

      if (res && res.run_id) {
        router.push(`/run/${res.run_id}`);
      } else {
        throw new Error("No run identifier was returned by the audit server.");
      }
    } catch (err: unknown) {
      setIsSubmitting(false);
      if (err instanceof ApiClientError) {
        setSubmitError(err.message);
      } else if (err instanceof Error) {
        setSubmitError(err.message);
      } else {
        setSubmitError("An unexpected error occurred while contacting the audit server.");
      }
    }
  }

  const isFormValid =
    (service.trim() || searchTerm.trim()) &&
    !urlError &&
    permissionConfirmed &&
    accountConfirmed;

  return (
    <form
      onSubmit={handleSubmit}
      className="exitlens-card p-6 sm:p-8 bg-white border border-[#E8E5DC] space-y-6"
    >
      {/* Error Banner */}
      {submitError && (
        <div
          role="alert"
          className="p-3.5 rounded-lg bg-[#FEF2F2] border border-[#FECACA] flex items-start gap-2.5 text-xs text-[#991B1B]"
        >
          <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-semibold">Unable to start audit</p>
            <p className="text-[#B91C1C] leading-relaxed">{submitError}</p>
          </div>
        </div>
      )}

      {/* 1. Subscription Service Field */}
      <div className="space-y-1.5" ref={comboboxRef}>
        <div className="flex items-center justify-between">
          <label
            htmlFor="service-input"
            className="block text-sm font-medium text-[#191817]"
          >
            Subscription service <span className="text-[#DC2626]">*</span>
          </label>
        </div>

        <div className="relative">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-[#8C8780] absolute left-3.5 pointer-events-none" />
            <input
              id="service-input"
              ref={inputRef}
              type="text"
              role="combobox"
              aria-expanded={isOpen}
              aria-autocomplete="list"
              aria-controls={listboxId}
              aria-activedescendant={
                highlightedIndex >= 0 ? `service-opt-${highlightedIndex}` : undefined
              }
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setService("");
                setIsOpen(true);
                setHighlightedIndex(0);
              }}
              onFocus={() => setIsOpen(true)}
              onKeyDown={handleKeyDown}
              placeholder="Search or type a service..."
              autoComplete="off"
              className="w-full pl-10 pr-10 py-2.5 text-sm bg-white border border-[#E8E5DC] rounded-lg text-[#191817] placeholder-[#8C8780] focus:border-[#191817] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#191817] transition-colors duration-200"
            />
            <button
              type="button"
              tabIndex={-1}
              onClick={() => setIsOpen(!isOpen)}
              className="absolute right-2.5 p-1 text-[#8C8780] hover:text-[#191817] transition-colors duration-200"
              aria-label="Toggle options list"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>

          {/* Combobox Options List */}
          {isOpen && (
            <ul
              id={listboxId}
              ref={listboxRef}
              role="listbox"
              className="absolute z-30 w-full mt-1.5 max-h-60 overflow-auto bg-white border border-[#E8E5DC] rounded-xl shadow-dropdown py-1 text-sm"
            >
              {filteredServices.length > 0 ? (
                filteredServices.map((item, index) => {
                  const isSelected = service === item;
                  const isHighlighted = highlightedIndex === index;
                  return (
                    <li
                      key={item}
                      id={`service-opt-${index}`}
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => selectService(item)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      className={`px-3.5 py-2 cursor-pointer flex items-center justify-between text-xs sm:text-sm transition-colors duration-150 ${
                        isHighlighted
                          ? "bg-[#F3F1EA] text-[#191817]"
                          : isSelected
                          ? "bg-[#FAF9F7] text-[#191817] font-semibold"
                          : "text-[#524F4B]"
                      }`}
                    >
                      <span>{item}</span>
                      {isSelected && <Check className="w-4 h-4 text-[#047857]" />}
                    </li>
                  );
                })
              ) : (
                <li
                  onClick={() => selectService(searchTerm.trim())}
                  className="px-3.5 py-2.5 text-xs text-[#524F4B] hover:bg-[#F3F1EA] cursor-pointer flex items-center justify-between"
                >
                  <span>Use custom service: &quot;<strong>{searchTerm}</strong>&quot;</span>
                  <span className="text-[11px] text-[#8C8780]">Press Enter</span>
                </li>
              )}
            </ul>
          )}
        </div>

        {service && (
          <p className="text-xs text-[#047857] flex items-center gap-1 font-medium pt-0.5">
            <Check className="w-3.5 h-3.5" /> Selected target: <strong>{service}</strong>
          </p>
        )}
      </div>

      {/* 2. Starting URL Field */}
      <div className="space-y-1.5">
        <label
          htmlFor="start-url-input"
          className="block text-sm font-medium text-[#191817]"
        >
          Starting URL (optional)
        </label>
        <input
          id="start-url-input"
          type="url"
          value={startUrl}
          onChange={(e) => handleUrlChange(e.target.value)}
          placeholder="https://service.com/account/subscription"
          className={`w-full px-3.5 py-2.5 text-sm bg-white border rounded-lg text-[#191817] placeholder-[#8C8780] focus:border-[#191817] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#191817] transition-colors duration-200 ${
            urlError ? "border-[#DC2626]" : "border-[#E8E5DC]"
          }`}
        />
        {urlError ? (
          <p className="text-xs text-[#DC2626] flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {urlError}
          </p>
        ) : (
          <p className="text-xs text-[#8C8780] leading-relaxed">
            Optional. Leave empty to audit the local dark-pattern demonstration OTT service.
          </p>
        )}
      </div>

      {/* 3. Safety and Compliance Section (Lightweight separator layout) */}
      <div className="pt-4 border-t border-[#E8E5DC] space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#191817]">
          Safety &amp; compliance
        </h3>

        <div className="space-y-2.5">
          <label className="flex items-start gap-3 cursor-pointer text-xs text-[#524F4B] leading-relaxed select-none group">
            <input
              type="checkbox"
              checked={permissionConfirmed}
              onChange={(e) => setPermissionConfirmed(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded border-[#DCD8CB] text-[#191817] focus:ring-0 cursor-pointer"
            />
            <span className="group-hover:text-[#191817] transition-colors duration-200">
              I have permission to request this audit and understand that I must comply with the service&apos;s terms and applicable laws.
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer text-xs text-[#524F4B] leading-relaxed select-none group">
            <input
              type="checkbox"
              checked={accountConfirmed}
              onChange={(e) => setAccountConfirmed(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded border-[#DCD8CB] text-[#191817] focus:ring-0 cursor-pointer"
            />
            <span className="group-hover:text-[#191817] transition-colors duration-200">
              I confirm that any account used for testing is mine or that I am explicitly authorized to use it.
            </span>
          </label>
        </div>

        <div className="pt-2 text-[11px] text-[#8C8780] flex items-center gap-1.5">
          <Lock className="w-3.5 h-3.5 text-[#64615B] shrink-0" />
          <span>ExitLens never collects passwords, payment cards, or sensitive secrets.</span>
        </div>
      </div>

      {/* 4. Primary CTA */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={!isFormValid || isSubmitting}
          className={`w-full py-2.5 px-4 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors duration-200 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2 ${
            isFormValid && !isSubmitting
              ? "bg-[#191817] text-white hover:bg-[#2C2A28] cursor-pointer"
              : "bg-[#E8E5DC] text-[#8C8780] cursor-not-allowed"
          }`}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Initializing audit session...</span>
            </>
          ) : (
            <>
              <span>Start audit</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>

        {!isFormValid && (
          <p className="text-center text-[11px] text-[#8C8780] mt-2">
            {!service.trim() && !searchTerm.trim()
              ? "Specify a subscription service to proceed"
              : !permissionConfirmed || !accountConfirmed
              ? "Check both safety confirmations to enable audit"
              : "Complete required fields"}
          </p>
        )}
      </div>
    </form>
  );
}
export default CheckFrictionForm;
