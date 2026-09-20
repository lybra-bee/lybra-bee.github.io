'use client';

import { usePathname, useRouter } from 'next/navigation';
import { ChangeEvent } from 'react';

export default function LanguageSwitcher({ currentLang }: { currentLang: string }) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLanguageChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const newLocale = e.target.value;
    if (!pathname) return;

    // Replace the current locale segment with the new one
    const segments = pathname.split('/');
    segments[1] = newLocale; // /en/foo -> /ru/foo

    router.push(segments.join('/'));
  };

  return (
    <select
      value={currentLang}
      onChange={handleLanguageChange}
      className="bg-transparent border border-gray-600 rounded px-2 py-1 text-sm outline-none text-white focus:ring-1 focus:ring-white transition-colors"
      aria-label="Select language"
    >
      <option value="en" className="text-black">English</option>
      <option value="ru" className="text-black">Русский</option>
    </select>
  );
}
