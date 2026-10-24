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
import { createRun, ApiClientError, fetchPresets, fetchTestAccounts, ServicePreset, TestAccountPublic } from "@/lib/api";

const LOCAL_PRESETS: ServicePreset[] = [
  { id: "streamflix", service: "StreamFlix India", category: "Video OTT", demo_path: "/demo-site/", default_start_url: "https://help.netflix.com/en/node/407", default_test_account_ref: "tacct_streamflix_in", description: "StreamFlix India cancellation flow demo.", expected_outcome: "completed_with_evidence" },
  { id: "ganaplus", service: "GanaPlus Music", category: "Audio Streaming", demo_path: "/demo-site/music.html", default_start_url: "https://support.spotify.com/in-en/article/cancel-premium/", default_test_account_ref: "tacct_ganaplus_in", description: "GanaPlus Music cancellation flow demo.", expected_outcome: "completed_with_evidence" },
  { id: "quickcart", service: "QuickCart Pro", category: "Quick Commerce Membership", demo_path: "/demo-site/fair.html", default_start_url: "https://support.google.com/youtube/answer/6308278?hl=en-IN", default_test_account_ref: "tacct_quickcart_in", description: "QuickCart Pro cancellation benchmark demo.", expected_outcome: "completed_with_evidence" },
  { id: "cineveil", service: "CineVeil VIP", category: "Video OTT (Barrier Gate)", demo_path: "/demo-site/blocked.html", default_start_url: "https://www.netflix.com/youraccount", default_test_account_ref: "tacct_cineveil_in", description: "CineVeil VIP barrier handling demo.", expected_outcome: "human_required" },
];

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
  const [presets, setPresets] = useState<ServicePreset[]>(LOCAL_PRESETS);
  const [presetsUsingFallback, setPresetsUsingFallback] = useState(true);
  const [testAccounts, setTestAccounts] = useState<TestAccountPublic[]>([]);
  const [accountsLoadedFromServer, setAccountsLoadedFromServer] = useState(false);
  const [testAccountRef, setTestAccountRef] = useState("");
  const [useExternalUrl, setUseExternalUrl] = useState(false);
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

  useEffect(() => {
    let mounted = true;
    fetchPresets().then((items) => {
      if (mounted) {
        setPresets(items);
        setPresetsUsingFallback(false);
      }
    }).catch(() => {
      if (mounted) {
        setPresets(LOCAL_PRESETS);
        setPresetsUsingFallback(true);
      }
    });
    fetchTestAccounts().then((items) => {
      if (mounted) {
        setTestAccounts(items.filter((item) => item.kind === "dedicated_test"));
        setAccountsLoadedFromServer(true);
      }
    }).catch(() => {
      if (mounted) {
        setTestAccounts([]);
        setAccountsLoadedFromServer(false);
      }
    });
    return () => { mounted = false; };
  }, []);

  // Submission & Validation State
  const [urlError, setUrlError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Filtered services
  const serviceOptions = Array.from(new Set([...presets.map((item) => item.service), ...COMMON_SERVICES]));
  const filteredServices = serviceOptions.filter((s) =>
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
    const preset = presets.find((item) => item.service === name);
    setService(name);
    setSearchTerm(name);
    setTestAccountRef(preset?.default_test_account_ref || "");
    setPermissionConfirmed(false);
    setAccountConfirmed(false);
    setUseExternalUrl(false);
    setStartUrl("");
    setUrlError(null);
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

    if (!selectedPreset && !startUrl.trim()) {
      setSubmitError("A custom service needs an HTTPS starting URL. Without one, the backend would return deterministic demo data instead of auditing the selected service.");
      return;
    }

    if (!permissionConfirmed || !accountConfirmed) {
      setSubmitError("Both safety & compliance confirmations are required to proceed.");
      return;
    }

    const selectedAccount = testAccounts.find((account) => account.id === testAccountRef);
    if (!accountsLoadedFromServer || !selectedAccount || selectedAccount.kind !== "dedicated_test" || (selectedPreset && (selectedAccount.service !== selectedPreset.service || selectedAccount.id !== selectedPreset.default_test_account_ref))) {
      setSubmitError("A dedicated test account must be confirmed by the backend before an audit can start. Personal accounts are not allowed.");
      return;
    }

    if (!selectedPreset && startUrl.trim() && !selectedAccount.has_cloud_credentials) {
      setSubmitError("The backend has not confirmed a TinyFish profile or credential binding for this test account. Bind its dedicated test account in the backend before a live audit.");
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await createRun({
        service: chosenService,
        start_url: startUrl.trim() || undefined,
        human_approved: true,
        test_account_confirmed: true,
        test_account_ref: selectedAccount.id,
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

  const selectedPreset = presets.find((item) => item.service === service);
  const selectedAccount = testAccounts.find((account) => account.id === testAccountRef);
  const customServiceNeedsUrl = Boolean(service.trim() && !selectedPreset && !startUrl.trim());
  const customLiveAccountReady = Boolean(
    selectedPreset || !startUrl.trim() || selectedAccount?.has_cloud_credentials
  );

  const isFormValid =
    (service.trim() || searchTerm.trim()) &&
    !urlError &&
    !customServiceNeedsUrl &&
    permissionConfirmed &&
    accountConfirmed &&
    accountsLoadedFromServer &&
    customLiveAccountReady &&
    testAccounts.some((account) => account.id === testAccountRef && account.kind === "dedicated_test" && (!selectedPreset || (account.service === selectedPreset.service && account.id === selectedPreset.default_test_account_ref)));

  return (
    <form
      onSubmit={handleSubmit}
      className="exitlens-card p-6 sm:p-8 bg-white border border-[#E8E5DC] space-y-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
        <span className={`rounded-full px-2.5 py-1 font-medium ${presetsUsingFallback ? "bg-[#FEF3C7] text-[#92400E]" : "bg-[#D1FAE5] text-[#065F46]"}`}>
          {presetsUsingFallback ? "Offline browsing · local preset fallback" : "Presets loaded from backend"}
        </span>
        <span className="text-[#8C8780]">{accountsLoadedFromServer ? "Test-account registry connected" : "Test-account registry unavailable"}</span>
      </div>

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
                setTestAccountRef("");
                setPermissionConfirmed(false);
                setAccountConfirmed(false);
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

      {/* Server-managed account gate */}
      <div className="space-y-2">
        <label htmlFor="test-account-select" className="block text-sm font-medium text-[#191817]">
          Dedicated Test Account <span className="text-[#DC2626]">*</span>
        </label>
        <select
          id="test-account-select"
          value={testAccountRef}
          onChange={(event) => { setTestAccountRef(event.target.value); setAccountConfirmed(false); }}
          disabled={!accountsLoadedFromServer || testAccounts.length === 0}
          className="w-full px-3.5 py-2.5 text-sm bg-white border border-[#E8E5DC] rounded-lg text-[#191817] disabled:bg-[#F3F1EA]"
        >
          <option value="">{accountsLoadedFromServer ? "Select a registered test account" : "Waiting for backend account verification"}</option>
          {testAccounts.filter((account) => !selectedPreset || (account.id === selectedPreset.default_test_account_ref && account.service === selectedPreset.service)).map((account) => (
            <option key={account.id} value={account.id}>
              {account.service} · {account.masked_identifier} · {account.kind}
            </option>
          ))}
        </select>
        {testAccountRef && testAccounts.some((account) => account.id === testAccountRef) ? (
          <p className="text-xs text-[#047857] flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5" /> Server-listed dedicated test account: <strong>{testAccounts.find((account) => account.id === testAccountRef)?.masked_identifier}</strong>
          </p>
        ) : (
          <p className="text-xs text-[#92400E]">
            {accountsLoadedFromServer ? "Choose an account from the server registry. A preset’s default reference is not verification." : "The backend must confirm a dedicated test account before this audit can start. No personal account may be used."}
          </p>
        )}
        {selectedPreset && <p className="text-[11px] text-[#64615B]">Preset default account: {selectedPreset.default_test_account_ref || "none"}. Confirm the matching account above.</p>}
      </div>

      {/* 2. Starting URL Field */}
      <div className="space-y-1.5">
        <label
          htmlFor="start-url-input"
          className="block text-sm font-medium text-[#191817]"
        >
          Starting URL {selectedPreset ? "(optional for curated presets)" : service ? <span className="text-[#DC2626]">*</span> : "(required for custom services)"}
        </label>
        {selectedPreset?.default_start_url && (
          <label className="flex items-start gap-2 text-xs text-[#524F4B]">
            <input
              type="checkbox"
              checked={useExternalUrl}
              onChange={(event) => {
                const checked = event.target.checked;
                setUseExternalUrl(checked);
                handleUrlChange(checked ? String(selectedPreset.default_start_url) : "");
              }}
              className="mt-0.5"
            />
            <span>Use preset external URL for a live external audit ({selectedPreset.default_start_url})</span>
          </label>
        )}
        <input
          id="start-url-input"
          type="url"
          value={startUrl}
          onChange={(e) => { setUseExternalUrl(false); handleUrlChange(e.target.value); }}
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
            {selectedPreset
              ? "Leave empty to use the preset demo route. If the backend has no public tunnel configured, that route uses deterministic demo data. Add an HTTPS URL to request a live external browser run."
              : "Enter the HTTPS page where the approved dedicated account can begin this service’s subscription journey. Leaving this blank would produce deterministic demo data, so custom-service audits require a URL."}
          </p>
        )}
        {!selectedPreset && startUrl.trim() && selectedAccount && !selectedAccount.has_cloud_credentials && (
          <p className="text-xs text-[#B45309]">This account is server-listed, but no TinyFish cloud profile or credential binding is confirmed. A live account audit is disabled until it is bound.</p>
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
              I approve this audit using only the selected registered dedicated test account. I will not use a personal account.
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
              : customServiceNeedsUrl
              ? "Enter an HTTPS starting URL for this custom service"
              : !customLiveAccountReady
              ? "Bind a TinyFish cloud profile or credentials to the test account"
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
