"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { href: "/", label: "Ask", description: "Ask a university question" },
  { href: "/calendar", label: "Calendar", description: "Plan academic dates" },
] as const;

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link href="/" className="brand" aria-label="OpenUni home">
          <span className="brand-mark" aria-hidden="true">
            OU
          </span>
          <span className="brand-copy">
            <span className="brand-name">OpenUni</span>
            <span className="brand-tagline">Answers grounded in official sources</span>
          </span>
        </Link>

        <nav className="site-nav" aria-label="Primary">
          {navigation.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className="site-nav-link"
                aria-current={active ? "page" : undefined}
                title={item.description}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
