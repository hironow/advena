import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import type { FC } from 'react';

interface ScriptDisplayProps {
  radioShow: RadioShow;
}

export const ScriptDisplay: FC<ScriptDisplayProps> = ({ radioShow }) => {
  return (
    <>
      <p>this is script display</p>
    </>
  );
};
