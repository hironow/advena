'use client';

import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

import Script from 'next/script';
import { AudioProvider } from '@/components/visualizer/audio-context-provider';
import { useSession } from 'next-auth/react';
import { useEffect } from 'react';
import { useAtom, useSetAtom } from 'jotai';
import { userAtom } from '@/lib/state';
import { getUserSnapshot } from '@/lib/firestore/client';

export default function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const userId = session?.user?.id;

  const [user, setUser] = useAtom(userAtom);

  useEffect(() => {
    if (!userId) return;

    const unsubscribeUser = getUserSnapshot(userId, (data) => {
      console.log('[snapshot] user', data);
      setUser(data);
    });

    return () => {
      unsubscribeUser();
    };
  }, [userId]);

  // TODO: Implement cookieStore
  const isCollapsed = false; // cookieStore.get('sidebar:state')?.value !== 'true';

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"
        strategy="beforeInteractive"
      />
      <AudioProvider>
        <SidebarProvider defaultOpen={!isCollapsed}>
          <AppSidebar user={user || undefined} />
          <SidebarInset>{children}</SidebarInset>
        </SidebarProvider>
      </AudioProvider>
    </>
  );
}
