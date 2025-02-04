import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

import Script from 'next/script';
import { AudioProvider } from '@/components/visualizer/audio-context-provider';
import { useSession } from 'next-auth/react';

export const experimental_ppr = true;

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  // TODO: user を取得する必要あり
  const session = useSession();
  const isCollapsed = false; // cookieStore.get('sidebar:state')?.value !== 'true';

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"
        strategy="beforeInteractive"
      />
      <AudioProvider>
        <SidebarProvider defaultOpen={!isCollapsed}>
          <AppSidebar user={undefined} />
          <SidebarInset>{children}</SidebarInset>
        </SidebarProvider>
      </AudioProvider>
    </>
  );
}
