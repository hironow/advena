'use client';

import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

import Script from 'next/script';
import { useSession } from 'next-auth/react';
import { useEffect } from 'react';
import {
  getRadioShowsSnapshot,
  getUserSnapshot,
} from '@/lib/firestore/client-db';
import type { User } from '@/lib/firestore/generated/entity_user';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';
import { useAtom } from 'jotai';
import { radioShowsAtom, userAtom } from '@/lib/state';

export default function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const userId = session?.user?.id;

  const isLoggedIn = status === 'authenticated';

  const [user, setUser] = useAtom<User | null>(userAtom);
  const [radioShows, setRadioShows] = useAtom<RadioShow[]>(radioShowsAtom);

  useEffect(() => {
    if (!userId) return;

    const unsubscribeUser = getUserSnapshot(userId, (data) => {
      console.debug('[snapshot changed][user]');
      setUser(data);
    });

    return () => {
      unsubscribeUser();
    };
  }, [userId]);

  useEffect(() => {
    if (!userId) return;

    const unsubscribeRadioShows = getRadioShowsSnapshot((data) => {
      console.debug('[snapshot changed][radio_shows]');
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
      <SidebarProvider defaultOpen={!isCollapsed}>
        <AppSidebar user={user || undefined} radioShows={radioShows} />
        <SidebarInset>{children}</SidebarInset>
      </SidebarProvider>
    </>
  );
}
