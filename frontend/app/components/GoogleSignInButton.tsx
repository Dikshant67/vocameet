"use client";

import { signIn, signOut, useSession } from "next-auth/react";

export default function GoogleSignInButton() {
  const { data: session } = useSession();

  const googleButtonStyle = `
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background-color: white;
    border: 1px solid #dadce0;
    border-radius: 4px;
    padding: 10px 24px;
    font-size: 16px;
    color: #3c4043;
    font-weight: 500;
    box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3);
    cursor: pointer;
    transition: box-shadow 0.2s ease;
  `;

  const googleIconStyle = `
    height: 20px;
    width: 20px;
    margin-right: 12px;
  `;

  return (
    <div>
      {session ? (
        <>
          <p>Welcome, {session.user?.name}</p>
          <button style={{ ...buttonStyles }} onClick={() => signOut()}>
            Sign out
          </button>
        </>
      ) : (
        <button
          style={{ ...buttonStyles }}
          onClick={() => signIn('google')}
        >
          <img
            src="/google-icon.svg"
            alt="Google Logo"
            style={{ height: '20px', width: '20px', marginRight: '12px' }}
          />
          Sign in with Google
        </button>
      )}
    </div>
  );
}

const buttonStyles = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: '#fff',
  border: '1px solid #dadce0',
  borderRadius: '4px',
  padding: '10px 24px',
  fontSize: '16px',
  color: '#3c4043',
  fontWeight: 500,
  boxShadow: '0px 1px 2px rgba(60, 64, 67, 0.3)',
  cursor: 'pointer',
};
