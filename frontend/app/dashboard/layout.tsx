import { headers } from 'next/headers';
import { UserProvider } from '@/app/context/UserContext';
import Providers from '@/components/GoogleSessionProvider';
import { getAppConfig } from '@/lib/utils';
import GoogleSignInButton from '../components/GoogleSignInButton';
import { GoogleOAuthProvider } from '@react-oauth/google';
import NavBar from '@/components/ui/NavBar.tsx';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default async function AppLayout({ children }: AppLayoutProps) {
  return (
    <>
  <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}
  
  
  
  >
 <UserProvider>
        <Providers>
          <header className="border-border sticky top-0 z-50 border-b bg-white/80 backdrop-blur-sm">
            {/* <div className="container mx-auto px-6 py-4"> */}
              {/* <div className="flex items-center justify-between"> */}
                {/* <div className="flex items-center space-x-3"> */}
                  {/* <div className="bg-gradient-voice flex h-9 w-9 items-center justify-center rounded-lg shadow-sm">
                    <span className="text-sm font-bold text-black">VA</span>
                  </div> */}
                  <NavBar/>
                  {/* <div>
                    <h1 className="text-xl font-bold text-black">Voice Agent</h1>
                    <p className="text-muted-black text-black">Meeting Management Platform</p>
                  </div> */}
                {/* </div> */}
                {/* <div className="flex items-center space-x-3"> */}
                
                {/* </div> */}
              {/* </div> */}
            {/* </div> */}
          </header>

          {children}
        </Providers>
      </UserProvider>
    </GoogleOAuthProvider>
     
    </>
  );
}
