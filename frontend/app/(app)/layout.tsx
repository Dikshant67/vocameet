import { headers } from 'next/headers';
import { getAppConfig } from '@/lib/utils';


interface AppLayoutProps {
  children: React.ReactNode;
}

export default async function AppLayout({ children }: AppLayoutProps) {
  const hdrs = await headers();
  const { companyName, logo, logoDark } = await getAppConfig(hdrs);
  


 
  return (
    <>
      <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 bg-gradient-voice rounded-lg flex items-center justify-center shadow-sm">
                  <span className="text-black font-bold text-sm">VA</span>
                </div>
                <div>
                  <h1 className="text-xl text-black font-bold ">Voice Agent</h1>
                  <p className="text-black text-muted-black">Meeting Management Platform</p>
                </div>
              </div>
            </div>
            
            <div className="w-72">
             
            </div>
          </div>
        </div>
      </header>
      {children}
    </>
  );
}
