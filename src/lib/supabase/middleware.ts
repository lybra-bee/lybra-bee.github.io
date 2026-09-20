import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder',
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // refreshing the auth token
  const { data: { user } } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;

  // We need to handle localization prefixes (e.g. /en/account, /ru/account)
  const isAccountRoute = pathname.match(/^\/(en|ru)\/account/);
  const isSellRoute = pathname.match(/^\/(en|ru)\/sell/);

  if (isAccountRoute || isSellRoute) {
    if (!user) {
      // no user, redirect to login with locale preserved
      const locale = pathname.split('/')[1];
      const url = request.nextUrl.clone();
      url.pathname = `/${locale}/login`;
      return NextResponse.redirect(url);
    }

    if (isSellRoute) {
      // Check if user is admin
      const { data: profile } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .single();

      if (!profile || profile.role !== 'admin') {
         // Not admin, maybe redirect to home or account
         const locale = pathname.split('/')[1];
         const url = request.nextUrl.clone();
         url.pathname = `/${locale}`;
         return NextResponse.redirect(url);
      }
    }
  }

  return supabaseResponse;
}
