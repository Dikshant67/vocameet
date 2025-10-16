import { headers } from 'next/headers';
import { App } from '@/components/app';
import { getAppConfig } from '@/lib/utils';
import Footer from '@/components/ui/Footer';

export default async function Page() {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return <>
  <App appConfig={appConfig} />
  <Footer/>
  </>
}
