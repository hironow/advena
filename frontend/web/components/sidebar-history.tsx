'use client';

import { isToday, isYesterday, subMonths, subWeeks } from 'date-fns';
import Link from 'next/link';
import { useParams, usePathname, useRouter } from 'next/navigation';
import type { User } from 'next-auth';
import { memo, useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';
import { useAtom } from 'jotai';
import { currentRadioShowIdAtom } from '@/lib/state';
import { DotGothic16 } from 'next/font/google';

const dotGothic16 = DotGothic16({
  weight: '400',
  subsets: ['latin'],
});

const PureRadioShowItem = ({
  radioShow,
  isActive,
  onRadioShowClick,
}: {
  radioShow: RadioShow;
  isActive: boolean;
  onRadioShowClick: (radioShow: RadioShow) => void;
}) => {
  const broadcastedDate = (radioShow.broadcasted_at as any).toDate();
  const displayDate = broadcastedDate
    ? broadcastedDate
    : (radioShow.created_at as any).toDate();

  // UTCなので日本時間に変換から表示
  const displayDateStr = displayDate.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
    // 時間も
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo',
  });

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive}>
        <Link
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onRadioShowClick(radioShow);
          }}
        >
          <span>{displayDateStr}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
};

export const RadioShowItem = memo(PureRadioShowItem, (prevProps, nextProps) => {
  if (prevProps.isActive !== nextProps.isActive) return false;
  return true;
});

export function SidebarHistory({
  user,
  radioShows,
}: { user: User | undefined; radioShows: RadioShow[] }) {
  const { setOpenMobile } = useSidebar();
  const pathname = usePathname();
  const router = useRouter();

  const [currentRadioShowId, setCurrentRadioShowId] = useAtom<string | null>(
    currentRadioShowIdAtom,
  );
  const id = currentRadioShowId;

  const handleRadioShowClick = (radioShow: RadioShow) => {
    setCurrentRadioShowId(radioShow.id);
    // sidebarを閉じる
    setOpenMobile(false);
  };

  if (!user) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div
            className="px-2 text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2"
            style={{
              fontFamily: dotGothic16.style.fontFamily,
            }}
          >
            ログインするとラジオが届きます
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  if (radioShows?.length === 0) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div
            className="px-2 text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2"
            style={{
              fontFamily: dotGothic16.style.fontFamily,
            }}
          >
            ラジオ番組がまだ届いていません
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  const groupRadioShowsByDate = (radioShows: RadioShow[]): any => {
    const now = new Date();
    const oneWeekAgo = subWeeks(now, 1);
    const oneMonthAgo = subMonths(now, 1);

    return radioShows.reduce(
      (groups, radioShow) => {
        let itemDate: Date;
        const createdDate = (radioShow.created_at as any).toDate();
        const broadcastedDate = (radioShow.broadcasted_at as any).toDate();
        // 基本は放送日を使うが、放送日がない場合は作成日を使う
        if (broadcastedDate) {
          itemDate = broadcastedDate;
        } else {
          itemDate = createdDate;
        }

        if (isToday(itemDate)) {
          groups.today.push(radioShow);
        } else if (isYesterday(itemDate)) {
          groups.yesterday.push(radioShow);
        } else if (itemDate > oneWeekAgo) {
          groups.lastWeek.push(radioShow);
        } else if (itemDate > oneMonthAgo) {
          groups.lastMonth.push(radioShow);
        } else {
          groups.older.push(radioShow);
        }

        return groups;
      },
      {
        today: [],
        yesterday: [],
        lastWeek: [],
        lastMonth: [],
        older: [],
      } as any,
    );
  };

  return (
    <>
      <SidebarGroup>
        <SidebarGroupContent>
          <SidebarMenu
            style={{
              fontFamily: dotGothic16.style.fontFamily,
            }}
          >
            {radioShows &&
              (() => {
                const groupedChats = groupRadioShowsByDate(radioShows);

                return (
                  <>
                    {groupedChats.today.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
                          Today
                        </div>
                        {groupedChats.today.map((radioShow: RadioShow) => (
                          <RadioShowItem
                            key={radioShow.id}
                            radioShow={radioShow}
                            isActive={radioShow.id === id}
                            onRadioShowClick={handleRadioShowClick}
                          />
                        ))}
                      </>
                    )}

                    {groupedChats.yesterday.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Yesterday
                        </div>
                        {groupedChats.yesterday.map((radioShow: RadioShow) => (
                          <RadioShowItem
                            key={radioShow.id}
                            radioShow={radioShow}
                            isActive={radioShow.id === id}
                            onRadioShowClick={handleRadioShowClick}
                          />
                        ))}
                      </>
                    )}

                    {groupedChats.lastWeek.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Last 7 days
                        </div>
                        {groupedChats.lastWeek.map((radioShow: RadioShow) => (
                          <RadioShowItem
                            key={radioShow.id}
                            radioShow={radioShow}
                            isActive={radioShow.id === id}
                            onRadioShowClick={handleRadioShowClick}
                          />
                        ))}
                      </>
                    )}

                    {groupedChats.lastMonth.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Last 30 days
                        </div>
                        {groupedChats.lastMonth.map((radioShow: RadioShow) => (
                          <RadioShowItem
                            key={radioShow.id}
                            radioShow={radioShow}
                            isActive={radioShow.id === id}
                            onRadioShowClick={handleRadioShowClick}
                          />
                        ))}
                      </>
                    )}

                    {groupedChats.older.length > 0 && (
                      <>
                        <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                          Older
                        </div>
                        {groupedChats.older.map((radioShow: RadioShow) => (
                          <RadioShowItem
                            key={radioShow.id}
                            radioShow={radioShow}
                            isActive={radioShow.id === id}
                            onRadioShowClick={handleRadioShowClick}
                          />
                        ))}
                      </>
                    )}
                  </>
                );
              })()}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </>
  );
}
