/** Typed client generated from the same OpenAPI contract as the FastAPI API. */
import createClient from 'openapi-fetch';
import type {paths} from './schema';

const baseUrl=import.meta.env.VITE_API_URL||(import.meta.env.DEV?'http://localhost:8000':'/api');
export const typedApi=createClient<paths>({baseUrl});

typedApi.use({
  async onRequest({request}) {
    const token=sessionStorage.getItem('gigbid_token');
    if(token)request.headers.set('Authorization',`Bearer ${token}`);
    return request;
  },
});
