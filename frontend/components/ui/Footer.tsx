import { Separator } from '@radix-ui/react-separator';
export default function Footer() {

    return ( <footer className="border-border w-full border-t  border-gray-300 bg-gray-100 fixed bottom-0 left-0 z-50 w-full">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-center space-x-4 text-sm leading-4">
              <span>&copy; 2025 TeknoLabs Voice Agent. Enterprise Meeting Management.</span>
              <Separator orientation="vertical" className="h-4" />
              <span>Powered by AI</span>
              <Separator orientation="vertical" className="h-4" />
              <span>Secure & Compliant</span>
              <Separator orientation="vertical" className="h-4" />
              <span>Built with TeknoLabs</span>
            </div>
          </div>
        </footer>)}