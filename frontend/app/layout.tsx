import "./globals.css";
import { Providers } from "@/components/Providers";
import { Shell } from "@/components/Shell";

export const metadata = { title: "StewardRail", description: "Neutral spending authority for shared AI treasuries." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><Providers><Shell>{children}</Shell></Providers></body></html>;
}
