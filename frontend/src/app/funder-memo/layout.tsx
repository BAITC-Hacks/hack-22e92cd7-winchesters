import { SiteNav } from "@/components/site/SiteNav";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteNav />
      {children}
    </>
  );
}
