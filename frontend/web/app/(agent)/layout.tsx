'use client';

import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

import Script from 'next/script';
import { AudioProvider } from '@/components/visualizer/audio-context-provider';
import { useSession } from 'next-auth/react';
import { useEffect, useState } from 'react';
import {
  getRadioShowsSnapshot,
  getUserSnapshot,
} from '@/lib/firestore/client-db';
import type { User } from '@/lib/firestore/generated/entity_user';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

export default function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const userId = session?.user?.id;

  const isLoggedIn = status === 'authenticated';
  console.info('isLoggedIn', isLoggedIn);

  const [user, setUser] = useState<User | null>(null);
  const [radioShows, setRadioShows] = useState<RadioShow[]>([]);

  useEffect(() => {
    if (!userId) return;

    const unsubscribeUser = getUserSnapshot(userId, (data) => {
      console.info('[snapshot changed] user', data);
      setUser(data);
    });

    return () => {
      unsubscribeUser();
    };
  }, [userId]);

  useEffect(() => {
    if (!userId) return;

    const unsubscribeRadioShows = getRadioShowsSnapshot((data) => {
      console.info('[snapshot changed] radio shows', data);
      setRadioShows(data);
    });

    return () => {
      unsubscribeRadioShows();
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
          <AppSidebar user={user || undefined} radioShows={radioShows} />
          <SidebarInset>{children}</SidebarInset>
        </SidebarProvider>
      </AudioProvider>
    </>
  );
}
