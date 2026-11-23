import json,glob,html,re
D='/home/claude/toolkit-scout/data/'
def corpus(i):
    s=''
    for f in [D+f'evidence/{i}.txt']+sorted(glob.glob(D+f'evidence_extra/{i}_*.txt')):
        s+=' '+open(f).read()
    s=html.unescape(s); return re.sub(r'\s+',' ',s)
def E(f,u,q): return {"field":f,"url":u,"quote":q,"src":"file"}
apps=[]
def add(**k): apps.append(k)
add(id=61,name="GitHub",entity_status="resolved",entity_note="GitHub.com REST and GraphQL APIs; GHES and GHEC data residency also exist.",
 description="Code hosting, issues, pull requests, Actions and developer platform APIs.",
 auth=["oauth2","bearer_token"],access_dev="self_free",access_prod="same_as_dev",min_plan="Free (personal account)",admin_only_credential=False,
 api_styles=["rest","graphql"],api_breadth="broad",api_beta=False,tenancy="global",mcp_type="official_remote",mcp_url="https://api.githubcopilot.com/mcp/",
 docs_url="https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api",
 ev=[("auth","https://docs.github.com/en/rest/quickstart","Create an access token. For example, create a personal access token or a GitHub App user access token."),
 ("auth","https://docs.github.com/llms.txt","You can connect your GitHub identity to third-party applications using OAuth."),
 ("access","https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api","You can authenticate to the REST API to access more endpoints and have a higher rate limit."),
 ("mcp","https://github.com/github/github-mcp-server","The remote GitHub MCP Server is hosted by GitHub and provides the easiest method for getting up and running."),
 ("api","https://docs.github.com/llms.txt","APIs (REST and GraphQL) for automation and integration")],
 confidence="medium",needs_human="Free-plan self-signup is not quoted on a fetched primary page; access_dev relies on well-known PAT creation. Confirm GitHub Apps/OAuth apps need no marketplace review for other orgs.")
add(id=62,name="Vercel",entity_status="resolved",entity_note="Vercel REST API.",
 description="Frontend cloud platform: deployments, projects, domains, logs via REST API and SDK.",
 auth=["bearer_token","oauth2"],access_dev="self_free",access_prod="same_as_dev",min_plan="Hobby (free, non-commercial); Pro $20/mo",admin_only_credential=False,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="global",mcp_type="official_remote",mcp_url="https://mcp.vercel.com",
 docs_url="https://vercel.com/docs/rest-api",
 ev=[("auth","https://vercel.com/llms.txt","Create scoped access tokens and send them as Bearer tokens."),
 ("auth","https://vercel.com/llms.txt","For Vercel MCP, use an OAuth-capable MCP client and let the user authorize access to their Vercel account."),
 ("access","https://vercel.com/pricing.md","Hobby is free for personal, non-commercial projects."),
 ("mcp","https://vercel.com/llms.txt","OAuth-authenticated tools for docs, projects, deployments, and logs, at `https://mcp.vercel.com`.")],
 confidence="high",needs_human="Hobby is non-commercial only; a commercial toolkit test likely needs Pro. REST OAuth for third-party apps goes through Vercel Integrations (not verified in fetched text).")
add(id=63,name="Netlify",entity_status="resolved",entity_note="Original seed URL 404s; current Netlify API quickstart is get-started-with-api.",
 description="Web hosting and deploy platform with REST API for sites, deploys, forms, DNS.",
 auth=["oauth2","bearer_token"],access_dev="self_free",access_prod="same_as_dev",min_plan="Free",admin_only_credential=False,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="global",mcp_type="official_remote",mcp_url="https://mcp.netlify.com/mcp",
 docs_url="https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/",
 ev=[("auth","https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api.md","Netlify uses OAuth2 for authentication. All requests must use HTTPS."),
 ("auth","https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api.md","If you're making a public integration with Netlify for others to enjoy, you must use OAuth2."),
 ("access","https://www.netlify.com/pricing/","Free forever. Build and deploy free forever."),
 ("mcp","https://docs.netlify.com/llms.txt","The Netlify MCP Server lets code agents create projects, deploy sites, manage environment variables, and more using the Netlify API and CLI."),
 ("mcp","https://docs.netlify.com/llms.txt","claude mcp add --transport http netlify https://mcp.netlify.com/mcp")],
 confidence="high",needs_human=None)
add(id=64,name="Cloudflare",entity_status="resolved",entity_note="Cloudflare v4 API (api.cloudflare.com/client/v4).",
 description="CDN, DNS, security, Workers and Zero Trust platform with a very large REST API.",
 auth=["bearer_token","api_key"],access_dev="self_free",access_prod="same_as_dev",min_plan="Free",admin_only_credential=False,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="global",mcp_type="official_remote",mcp_url="https://mcp.cloudflare.com/mcp",
 docs_url="https://developers.cloudflare.com/fundamentals/api/get-started/create-token/",
 ev=[("auth","https://developers.cloudflare.com/api/resources/accounts/subresources/tokens/","API Token The preferred authorization scheme for interacting with the Cloudflare API. Create a token . Example: Authorization: Bearer"),
 ("auth","https://developers.cloudflare.com/api/","reading, updating, or deleting an Organization requires a Global API key and your registered email address."),
 ("access","https://www.cloudflare.com/plans/","Free For personal or hobby projects that aren't business-critical. $0 /month"),
 ("mcp","https://github.com/cloudflare/mcp-server-cloudflare","Cloudflare offers the following MCP servers."),
 ("mcp","https://github.com/cloudflare/mcp-server-cloudflare","`https://mcp.cloudflare.com/mcp`")],
 confidence="high",needs_human=None)
add(id=65,name="Supabase",entity_status="resolved",entity_note="Supabase Management API (projects/org management); per-project data APIs (PostgREST etc.) are separate.",
 description="Postgres-based backend platform; Management API controls orgs, projects, branches and config.",
 auth=["bearer_token","oauth2"],access_dev="self_free",access_prod="same_as_dev",min_plan="Free",admin_only_credential=False,
 api_styles=["rest"],api_breadth="moderate",api_beta=False,tenancy="global",mcp_type="official_remote",mcp_url="https://mcp.supabase.com/mcp",
 docs_url="https://supabase.com/docs/reference/api/introduction",
 ev=[("auth","https://supabase.com/docs/reference/api/introduction","All API requests require an access token to be included in the Authorization header"),
 ("auth","https://supabase.com/docs/reference/api/introduction","OAuth2 allows your application to generate tokens on behalf of a Supabase user"),
 ("access","https://supabase.com/pricing","Start building for free, collaborate with your team, then scale to millions of users"),
 ("mcp","https://supabase.com/llms.txt","Streamable HTTP MCP endpoint, OAuth-protected, for managing projects, database schema, and queries from MCP clients")],
 confidence="high",needs_human=None)
add(id=66,name="Neo4j",entity_status="resolved",entity_note="Interpreted as Neo4j Aura API (api.neo4j.io) for instance management; database data access is via per-instance Bolt/HTTP Query API endpoints.",
 description="Graph database; Aura API manages cloud instances, separate Bolt/Query API for data.",
 auth=["oauth2","basic","bearer_token"],access_dev="self_free",access_prod="same_as_dev",min_plan="AuraDB Free (no credit card)",admin_only_credential=False,
 api_styles=["rest"],api_breadth="narrow",api_beta=False,tenancy="global",mcp_type="official_local",mcp_url="https://neo4j.com/docs/mcp/current/",
 docs_url="https://neo4j.com/docs/aura/api/authentication/",
 ev=[("auth","https://neo4j.com/docs/aura/api/authentication/","you must provide a Bearer Token in the Authorization header of each request"),
 ("auth","https://neo4j.com/docs/aura/api/authentication/","Authentication to the token endpoint uses HTTP Basic Authentication"),
 ("access","https://neo4j.com/llms.txt","(recommended, no credit card): https://neo4j.com/cloud/aura-free/"),
 ("mcp","https://neo4j.com/docs/mcp/current/","Neo4j MCP implements the Model Context Protocol (MCP), an open standard that lets applications connect to external data sources and tools."),
 ("api","https://neo4j.com/docs/aura/api/overview/","The current version of the Aura API is v1")],
 confidence="medium",needs_human="Aura API manages instances only; data access is per-instance Bolt/Query API. Which surface should the toolkit target? Also confirm whether a hosted remote Neo4j MCP exists (only local server found).")
add(id=67,name="Snowflake",entity_status="resolved",entity_note="Snowflake SQL API plus Snowflake-managed MCP server; endpoints are per-account URLs.",
 description="Cloud data platform; SQL API executes statements over REST per account.",
 auth=["oauth2","jwt","other"],access_dev="self_trial",access_prod="customer_only",min_plan="Free trial; paid on-demand after",admin_only_credential=None,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="per_subdomain",mcp_type="official_remote",
 mcp_url="https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp",
 docs_url="https://docs.snowflake.com/developer-guide/sql-api/authenticating",
 ev=[("auth","https://docs.snowflake.com/en/developer-guide/sql-api/index","Use OAuth or Key Pair to authenticate with the Snowflake server."),
 ("auth","https://docs.snowflake.com/developer-guide/sql-api/authenticating","KEYPAIR_JWT (for key-pair authentication) OAUTH (for OAuth) PROGRAMMATIC_ACCESS_TOKEN (for programmatic access tokens )"),
 ("access","https://docs.snowflake.com/en/user-guide/admin-trial-account","You can sign up for a free trial using the self-service form"),
 ("mcp","https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp","The Snowflake-managed MCP server lets AI agents securely retrieve data from Snowflake accounts without needing to deploy separate infrastructure."),
 ("mcp","https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp","https://<account_url>/api/v2/databases/{database}/schemas/{schema}/mcp-servers/{name}")],
 confidence="high",needs_human="Production use is inside each customer's own Snowflake account (account-specific URL, OAuth/key-pair setup by customer admin). Trial limitations not reviewed.")
add(id=68,name="MongoDB Atlas",entity_status="resolved",entity_note="Atlas Administration API (control plane); does not access cluster data.",
 description="Managed MongoDB cloud; Admin API manages clusters, projects, users and access.",
 auth=["oauth2","other"],access_dev="self_free",access_prod="same_as_dev",min_plan="Free (M0) tier",admin_only_credential=True,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="global",mcp_type="official_remote",
 mcp_url="https://www.mongodb.com/docs/mcp-server/overview/",
 docs_url="https://www.mongodb.com/docs/atlas/api/api-authentication/",
 ev=[("auth","https://www.mongodb.com/docs/atlas/api/api-authentication/","We recommend you use service accounts instead of API keys to authenticate to the Atlas Administration API."),
 ("auth","https://www.mongodb.com/docs/atlas/api/api-authentication/","Service account access tokens ( OAuth 2.0) API keys ( HTTP Digest Authentication)"),
 ("access","https://www.mongodb.com/docs/atlas/configure-api-access/","To create a service account or API keys for an organization, you must have Organization Owner access to that organization."),
 ("access","https://www.mongodb.com/pricing","Get started for free in minutes"),
 ("mcp","https://www.mongodb.com/docs/mcp-server/overview/","MongoDB Atlas Managed MCP Server, which MongoDB hosts and manages for you in Atlas.")],
 confidence="medium",needs_human="Atlas Managed MCP Server is described as public preview; confirm hosted URL and GA status. Remote vs local both official.")
add(id=69,name="Datadog",entity_status="resolved",entity_note="Datadog REST API; regional sites (US1, US3, US5, EU, AP1, AP2, UK1, gov).",
 description="Observability and security platform; REST API for metrics, logs, monitors, dashboards, incidents.",
 auth=["api_key","oauth2"],access_dev="self_trial",access_prod="customer_only",min_plan="Free trial (paid plans after)",admin_only_credential=None,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="per_region",mcp_type="official_remote",
 mcp_url="https://docs.datadoghq.com/bits_ai/mcp_server/",
 docs_url="https://docs.datadoghq.com/api/latest/",
 ev=[("auth","https://docs.datadoghq.com/api/latest/","Authenticate to the API with an API key using the header DD-API-KEY . For some endpoints, you also need an Application key"),
 ("auth","https://docs.datadoghq.com/api/latest/","Authorization Scopes for OAuth Clients"),
 ("access","https://docs.datadoghq.com/api/latest/","GET STARTED FREE Free Trial"),
 ("mcp","https://docs.datadoghq.com/bits_ai/mcp_server/","The Datadog MCP Server acts as a bridge between your observability data in Datadog and any AI agents that support the Model Context Protocol (MCP)"),
 ("mcp","https://docs.datadoghq.com/bits_ai/mcp_server/","It provides remote access to most Datadog products")],
 confidence="medium",needs_human="Free trial duration and who can create API/app keys (admin permission) not verified; remote MCP endpoint URL not captured; production OAuth client registration process unclear. MCP page text says not supported on some sites (e.g. GovCloud).")
add(id=70,name="Sentry",entity_status="resolved",entity_note="Sentry Web API (sentry.io/api/0), region-specific domains (US/DE) exist; self-hosted also supported.",
 description="Error and performance monitoring; REST API for orgs, projects, issues, events, releases.",
 auth=["bearer_token","oauth2"],access_dev="self_free",access_prod="same_as_dev",min_plan="Free (Developer) plan",admin_only_credential=False,
 api_styles=["rest"],api_breadth="broad",api_beta=False,tenancy="per_region",mcp_type="official_remote",mcp_url="https://mcp.sentry.dev/mcp",
 docs_url="https://docs.sentry.io/api/auth/",
 ev=[("auth","https://docs.sentry.io/api/auth/","You can create authentication tokens within Sentry by creating an internal integration ."),
 ("auth","https://docs.sentry.io/api/auth/","Sentry supports OAuth2 with the authorization code grant type."),
 ("access","https://docs.sentry.io/llms.txt","Plans, free monthly quotas per feature, trial details, and pay-as-you-go pricing for individual SKUs."),
 ("mcp","https://docs.sentry.io/ai/mcp/","The base MCP server address is: https://mcp.sentry.dev/mcp")],
 confidence="medium",needs_human="Free-plan self-signup quote is indirect (pricing llms.txt line). Creating an internal integration may need org manager/owner role; not verified.")
out=[];bad=0
for a in apps:
    c=corpus(a['id']); ev=[]
    for f,u,q in a.pop('ev'):
        if re.sub(r'\s+',' ',html.unescape(q)) not in c: print('MISSING',a['id'],q[:70]); bad+=1
        assert len(q.split())<=32,(a['id'],q)
        ev.append(E(f,u,q))
    a['evidence']=ev; out.append(a)
print('bad',bad)
open('/tmp/out61.jsonl','w').write('\n'.join(json.dumps(a,ensure_ascii=False) for a in out)+'\n')
