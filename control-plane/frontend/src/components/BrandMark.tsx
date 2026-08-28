import { useId } from "react";

import { cn } from "@/lib/utils";

export function BrandMark({
  className,
  title,
}: {
  className?: string;
  title?: string;
}) {
  const gradientId = useId();

  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={cn("shrink-0", className)}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
    >
      {title && <title>{title}</title>}
      <defs>
        <linearGradient
          id={gradientId}
          x1="13"
          y1="12"
          x2="52"
          y2="53"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#67E8D5" />
          <stop offset="1" stopColor="#2BB7D6" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill="#111B25" />
      <path
        d="M32 8.5 52.35 20.25v23.5L32 55.5 11.65 43.75v-23.5L32 8.5Z"
        fill="#67E8D5"
        fillOpacity=".05"
        stroke={`url(#${gradientId})`}
        strokeWidth="2.5"
      />
      <path
        d="m18.25 23.9 13.75-8 13.75 8L32 31.9l-13.75-8Z"
        fill="#67E8D5"
        fillOpacity=".18"
        stroke={`url(#${gradientId})`}
        strokeWidth="2.25"
        strokeLinejoin="round"
      />
      <path
        d="M18.25 23.9v16.2L32 48V31.9l-13.75-8Z"
        fill="#2BB7D6"
        fillOpacity=".12"
        stroke={`url(#${gradientId})`}
        strokeWidth="2.25"
        strokeLinejoin="round"
      />
      <path
        d="M45.75 23.9v16.2L32 48V31.9l13.75-8Z"
        fill="#67E8D5"
        fillOpacity=".08"
        stroke={`url(#${gradientId})`}
        strokeWidth="2.25"
        strokeLinejoin="round"
      />
      <circle cx="18.25" cy="23.9" r="2.3" fill="#A7F3E8" />
      <circle cx="45.75" cy="23.9" r="2.3" fill="#50D8E4" />
      <circle cx="32" cy="48" r="2.3" fill="#67E8D5" />
    </svg>
  );
}
