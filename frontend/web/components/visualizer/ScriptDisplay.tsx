import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import type { FC } from 'react';
import {
  AttachmentIcon,
  BoxIcon,
  ChevronDownIcon,
  CrossIcon,
  CrossSmallIcon,
  GlobeIcon,
  InfoIcon,
  InvoiceIcon,
  LoaderIcon,
  LogoGoogle,
  LogsIcon,
  MenuIcon,
  MoreHorizontalIcon,
  MoreIcon,
  PenIcon,
  PlayIcon,
  RouteIcon,
  StopIcon,
  SummarizeIcon,
} from '../icons';
import { Button } from '../ui/button';

interface ScriptDisplayProps {
  radioShow: RadioShow;
}

export const ScriptDisplay: FC<ScriptDisplayProps> = ({ radioShow }) => {
  return (
    <>
      <Button>
        <GlobeIcon />
      </Button>
      <Button>
        <LogsIcon />
      </Button>
      <Button>
        <InfoIcon />
      </Button>
      <p>this is script display</p>
    </>
  );
};
