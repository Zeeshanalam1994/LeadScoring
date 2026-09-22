import type { EquipmentKind } from "./types";

const stroke = "#2c3e50";
const fill = "#e8ecf0";

export function EquipmentIcon({ kind, size = 40 }: { kind: EquipmentKind; size?: number }) {
  switch (kind) {
    case "column":
      return (
        <svg width={size} height={size * 1.4} viewBox="0 0 48 68" aria-hidden>
          <rect x="14" y="4" width="20" height="60" fill={fill} stroke={stroke} strokeWidth="2" />
          <line x1="8" y1="18" x2="14" y2="18" stroke={stroke} strokeWidth="2" />
          <line x1="34" y1="28" x2="40" y2="28" stroke={stroke} strokeWidth="2" />
          <line x1="8" y1="38" x2="14" y2="38" stroke={stroke} strokeWidth="2" />
          <line x1="34" y1="48" x2="40" y2="48" stroke={stroke} strokeWidth="2" />
          <line x1="8" y1="58" x2="14" y2="58" stroke={stroke} strokeWidth="2" />
        </svg>
      );
    case "reactor":
      return (
        <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden>
          <ellipse cx="24" cy="10" rx="16" ry="6" fill={fill} stroke={stroke} strokeWidth="2" />
          <path d="M8 10 v22 a16 10 0 0 0 32 0 V10" fill={fill} stroke={stroke} strokeWidth="2" />
          <rect x="20" y="32" width="8" height="12" fill={fill} stroke={stroke} strokeWidth="2" />
        </svg>
      );
    case "heater":
      return (
        <svg width={size} height={size * 0.7} viewBox="0 0 56 36" aria-hidden>
          <rect x="4" y="10" width="48" height="18" rx="3" fill="#fff3e0" stroke="#e65100" strokeWidth="2" />
          <path d="M12 19 h32" stroke="#e65100" strokeWidth="2" strokeDasharray="4 3" />
          <text x="28" y="22" textAnchor="middle" fontSize="8" fill="#e65100">🔥</text>
        </svg>
      );
    case "tank":
      return (
        <svg width={size} height={size * 0.85} viewBox="0 0 48 42" aria-hidden>
          <ellipse cx="24" cy="10" rx="18" ry="7" fill={fill} stroke={stroke} strokeWidth="2" />
          <path d="M6 10 v16 a18 8 0 0 0 36 0 V10" fill={fill} stroke={stroke} strokeWidth="2" />
        </svg>
      );
    case "blender":
      return (
        <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden>
          <circle cx="24" cy="24" r="18" fill="#e3f2fd" stroke="#1565c0" strokeWidth="2" />
          <path d="M14 24 h20 M24 14 v20" stroke="#1565c0" strokeWidth="2" />
        </svg>
      );
    case "feeder":
      return (
        <svg width={size} height={size * 0.6} viewBox="0 0 48 28" aria-hidden>
          <path d="M4 14 H36 L28 6 M36 14 L28 22" fill="none" stroke="#2e7d32" strokeWidth="2.5" />
        </svg>
      );
    default:
      return (
        <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden>
          <rect x="8" y="12" width="32" height="24" rx="4" fill={fill} stroke={stroke} strokeWidth="2" />
        </svg>
      );
  }
}
