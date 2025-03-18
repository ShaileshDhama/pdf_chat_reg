import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from './index';

export const api = createApi({
    reducerPath: 'api',
    baseQuery: fetchBaseQuery({
        baseUrl: '/api',
        prepareHeaders: (headers, { getState }) => {
            const token = (getState() as RootState).auth.token;
            if (token) {
                headers.set('authorization', `Bearer ${token}`);
            }
            return headers;
        },
    }),
    tagTypes: ['Documents', 'Profile'],
    endpoints: (builder) => ({
        // Auth endpoints
        getNonce: builder.query<{ nonce: string }, string>({
            query: (address) => `/auth/nonce?address=${address}`,
        }),
        verifySignature: builder.mutation<
            { token: string; user: any },
            { address: string; signature: string }
        >({
            query: (credentials) => ({
                url: '/auth/verify',
                method: 'POST',
                body: credentials,
            }),
        }),

        // Document endpoints
        getDocuments: builder.query<any[], void>({
            query: () => '/documents',
            providesTags: ['Documents'],
        }),
        getDocument: builder.query<any, string>({
            query: (id) => `/documents/${id}`,
            providesTags: (result, error, id) => [{ type: 'Documents', id }],
        }),
        uploadDocument: builder.mutation<any, FormData>({
            query: (data) => ({
                url: '/documents/upload',
                method: 'POST',
                body: data,
            }),
            invalidatesTags: ['Documents'],
        }),
        analyzeDocument: builder.mutation<any, { id: string; query?: string }>({
            query: ({ id, query }) => ({
                url: `/documents/${id}/analyze`,
                method: 'POST',
                body: { query },
            }),
        }),
        verifyDocument: builder.mutation<any, string>({
            query: (id) => ({
                url: `/documents/${id}/verify`,
                method: 'POST',
            }),
        }),
        shareDocument: builder.mutation<
            any,
            { id: string; address: string; encryptedKey: string }
        >({
            query: ({ id, ...body }) => ({
                url: `/documents/${id}/share`,
                method: 'POST',
                body,
            }),
            invalidatesTags: (result, error, { id }) => [
                { type: 'Documents', id },
            ],
        }),
        revokeAccess: builder.mutation<
            any,
            { id: string; address: string }
        >({
            query: ({ id, address }) => ({
                url: `/documents/${id}/revoke`,
                method: 'POST',
                body: { address },
            }),
            invalidatesTags: (result, error, { id }) => [
                { type: 'Documents', id },
            ],
        }),

        // Profile endpoints
        getProfile: builder.query<any, void>({
            query: () => '/profile',
            providesTags: ['Profile'],
        }),
        updateProfile: builder.mutation<
            any,
            {
                name: string;
                organization: string;
                licenseNumber?: string;
                metadataURI?: string;
            }
        >({
            query: (data) => ({
                url: '/profile',
                method: 'PUT',
                body: data,
            }),
            invalidatesTags: ['Profile'],
        }),

        // Blockchain endpoints
        getGasPrice: builder.query<string, void>({
            query: () => '/blockchain/gas-price',
        }),
        estimateGas: builder.query<
            string,
            { operation: string; params: any }
        >({
            query: ({ operation, params }) => ({
                url: '/blockchain/estimate-gas',
                method: 'POST',
                body: { operation, params },
            }),
        }),
    }),
});

export const {
    useGetNonceQuery,
    useVerifySignatureMutation,
    useGetDocumentsQuery,
    useGetDocumentQuery,
    useUploadDocumentMutation,
    useAnalyzeDocumentMutation,
    useVerifyDocumentMutation,
    useShareDocumentMutation,
    useRevokeAccessMutation,
    useGetProfileQuery,
    useUpdateProfileMutation,
    useGetGasPriceQuery,
    useEstimateGasQuery,
} = api;
