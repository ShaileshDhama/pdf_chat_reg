import React, { useEffect, useState } from 'react';
import { useWeb3Modal } from '@web3modal/react';
import { useAccount, useSignMessage, useDisconnect } from 'wagmi';
import { ethers } from 'ethers';

interface Web3AuthProps {
    onAuthSuccess: (token: string) => void;
    onAuthError: (error: string) => void;
}

const Web3Auth: React.FC<Web3AuthProps> = ({ onAuthSuccess, onAuthError }) => {
    const { open } = useWeb3Modal();
    const { address, isConnected } = useAccount();
    const { disconnect } = useDisconnect();
    const { signMessage } = useSignMessage();
    const [isAuthenticating, setIsAuthenticating] = useState(false);

    useEffect(() => {
        if (isConnected && address) {
            handleAuthentication();
        }
    }, [isConnected, address]);

    const handleAuthentication = async () => {
        if (!address) return;

        try {
            setIsAuthenticating(true);

            // Get nonce from backend
            const nonceResponse = await fetch(`/api/auth/nonce?address=${address}`);
            const { nonce } = await nonceResponse.json();

            // Sign message
            const signature = await signMessage({ message: nonce });

            // Verify signature with backend
            const verifyResponse = await fetch('/api/auth/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    address,
                    signature,
                }),
            });

            const result = await verifyResponse.json();

            if (result.success) {
                onAuthSuccess(result.token);
            } else {
                onAuthError(result.error || 'Authentication failed');
                disconnect();
            }
        } catch (error) {
            onAuthError(error.message);
            disconnect();
        } finally {
            setIsAuthenticating(false);
        }
    };

    const handleConnect = async () => {
        try {
            await open();
        } catch (error) {
            onAuthError(error.message);
        }
    };

    const handleDisconnect = () => {
        disconnect();
    };

    return (
        <div className="web3-auth">
            {!isConnected ? (
                <button
                    onClick={handleConnect}
                    className="connect-wallet-btn"
                    disabled={isAuthenticating}
                >
                    Connect Wallet
                </button>
            ) : (
                <div className="wallet-info">
                    <div className="address">
                        {`${address.slice(0, 6)}...${address.slice(-4)}`}
                    </div>
                    <button
                        onClick={handleDisconnect}
                        className="disconnect-btn"
                        disabled={isAuthenticating}
                    >
                        Disconnect
                    </button>
                </div>
            )}
            {isAuthenticating && (
                <div className="auth-status">
                    <div className="spinner"></div>
                    <span>Authenticating...</span>
                </div>
            )}
            <style jsx>{`
                .web3-auth {
                    padding: 1rem;
                    border-radius: 0.5rem;
                    background: #1a1a1a;
                    color: white;
                }

                .connect-wallet-btn,
                .disconnect-btn {
                    padding: 0.75rem 1.5rem;
                    border-radius: 0.375rem;
                    border: none;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .connect-wallet-btn {
                    background: #3b82f6;
                    color: white;
                }

                .connect-wallet-btn:hover {
                    background: #2563eb;
                }

                .disconnect-btn {
                    background: #dc2626;
                    color: white;
                }

                .disconnect-btn:hover {
                    background: #b91c1c;
                }

                .wallet-info {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }

                .address {
                    font-family: monospace;
                    padding: 0.5rem;
                    background: #2d2d2d;
                    border-radius: 0.25rem;
                }

                .auth-status {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin-top: 0.5rem;
                }

                .spinner {
                    width: 1rem;
                    height: 1rem;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #3b82f6;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                button:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }
            `}</style>
        </div>
    );
};

export default Web3Auth;
