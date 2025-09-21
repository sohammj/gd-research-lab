import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import { Geist , Poppins} from 'next/font/google'
const geist = Poppins({
  subsets: ['latin'],
  weight:['100','200','300','400','500','600','700','800']
})


export const metadata: Metadata = {
  title: "GD Research Lab",
  description: "AI mentor that critiques ideas, finds gaps, and plans next steps",
};


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={geist.className}>
      <body className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-black text-zinc-950 dark:text-zinc-150 antialiased">
        {children}
      </body>
    </html>
  );
}
