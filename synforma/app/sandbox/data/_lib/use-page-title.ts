"use client";
import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} · Nimbus Data Console` : "Nimbus Data Console";
  }, [title]);
}
