/**
 * className utility function
 * Combines class names, useful for conditional classes
 * 
 * Similar to clsx or classnames, but lightweight
 */

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
