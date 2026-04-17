--
-- PostgreSQL database dump
--

\restrict pqktbRRtcMpnqyeZYlwb2mIstoXhQ3AYDx6BkiXc70Wfq8OSLKTDx0KKwdb0wUS

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: accesslevel; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.accesslevel AS ENUM (
    'audio',
    'video',
    'blast_dial'
);


ALTER TYPE public.accesslevel OWNER TO postgres;

--
-- Name: membergroupaccesslevel; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.membergroupaccesslevel AS ENUM (
    'audio',
    'video',
    'blast_dial'
);


ALTER TYPE public.membergroupaccesslevel OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'super_admin',
    'admin',
    'agent',
    'viewer'
);


ALTER TYPE public.userrole OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groups (
    "UUID" uuid NOT NULL,
    name character varying(50) NOT NULL
);


ALTER TABLE public.groups OWNER TO postgres;

--
-- Name: meeting_group_association; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.meeting_group_association (
    meeting_id uuid NOT NULL,
    group_id uuid NOT NULL
);


ALTER TABLE public.meeting_group_association OWNER TO postgres;

--
-- Name: meetings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.meetings (
    "UUID" uuid NOT NULL,
    m_number character varying(15) NOT NULL,
    "accessLevel" public.accesslevel NOT NULL,
    password character varying(120)
);


ALTER TABLE public.meetings OWNER TO postgres;

--
-- Name: member_group_access; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.member_group_access (
    member_uuid uuid NOT NULL,
    group_uuid uuid NOT NULL,
    access_level public.membergroupaccesslevel NOT NULL
);


ALTER TABLE public.member_group_access OWNER TO postgres;

--
-- Name: used_refresh_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.used_refresh_tokens (
    jti character varying NOT NULL,
    user_uuid character varying,
    expires_at integer
);


ALTER TABLE public.used_refresh_tokens OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    "UUID" uuid NOT NULL,
    s_id character varying(50) NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(250) NOT NULL,
    role public.userrole NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.groups ("UUID", name) FROM stdin;
\.


--
-- Data for Name: meeting_group_association; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.meeting_group_association (meeting_id, group_id) FROM stdin;
\.


--
-- Data for Name: meetings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.meetings ("UUID", m_number, "accessLevel", password) FROM stdin;
\.


--
-- Data for Name: member_group_access; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.member_group_access (member_uuid, group_uuid, access_level) FROM stdin;
\.


--
-- Data for Name: used_refresh_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.used_refresh_tokens (jti, user_uuid, expires_at) FROM stdin;
a1412b1a-ba2b-4c40-8987-cf785c9d8ec8	a31ea1c9-0005-4faf-b97f-f61a4e6c1588	1776417466
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users ("UUID", s_id, username, password, role) FROM stdin;
a31ea1c9-0005-4faf-b97f-f61a4e6c1588	superadmin	superadmin	$argon2id$v=19$m=65536,t=3,p=4$+Z/z3vufc06pFeJ8DyEEYA$VqnYBqQ9hkU4HjhiZpcFDHprXQ4w81GtEGveN4BKMiw	super_admin
\.


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY ("UUID");


--
-- Name: meeting_group_association meeting_group_association_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.meeting_group_association
    ADD CONSTRAINT meeting_group_association_pkey PRIMARY KEY (meeting_id, group_id);


--
-- Name: meetings meetings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.meetings
    ADD CONSTRAINT meetings_pkey PRIMARY KEY ("UUID");


--
-- Name: member_group_access member_group_access_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member_group_access
    ADD CONSTRAINT member_group_access_pkey PRIMARY KEY (member_uuid, group_uuid, access_level);


--
-- Name: used_refresh_tokens used_refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.used_refresh_tokens
    ADD CONSTRAINT used_refresh_tokens_pkey PRIMARY KEY (jti);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY ("UUID");


--
-- Name: ix_groups_UUID; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_groups_UUID" ON public.groups USING btree ("UUID");


--
-- Name: ix_meetings_UUID; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_meetings_UUID" ON public.meetings USING btree ("UUID");


--
-- Name: ix_meetings_m_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_meetings_m_number ON public.meetings USING btree (m_number);


--
-- Name: ix_used_refresh_tokens_jti; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_used_refresh_tokens_jti ON public.used_refresh_tokens USING btree (jti);


--
-- Name: ix_used_refresh_tokens_user_uuid; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_used_refresh_tokens_user_uuid ON public.used_refresh_tokens USING btree (user_uuid);


--
-- Name: ix_users_UUID; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "ix_users_UUID" ON public.users USING btree ("UUID");


--
-- Name: ix_users_s_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_s_id ON public.users USING btree (s_id);


--
-- Name: meeting_group_association meeting_group_association_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.meeting_group_association
    ADD CONSTRAINT meeting_group_association_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups("UUID") ON DELETE CASCADE;


--
-- Name: meeting_group_association meeting_group_association_meeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.meeting_group_association
    ADD CONSTRAINT meeting_group_association_meeting_id_fkey FOREIGN KEY (meeting_id) REFERENCES public.meetings("UUID") ON DELETE CASCADE;


--
-- Name: member_group_access member_group_access_group_uuid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member_group_access
    ADD CONSTRAINT member_group_access_group_uuid_fkey FOREIGN KEY (group_uuid) REFERENCES public.groups("UUID") ON DELETE CASCADE;


--
-- Name: member_group_access member_group_access_member_uuid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member_group_access
    ADD CONSTRAINT member_group_access_member_uuid_fkey FOREIGN KEY (member_uuid) REFERENCES public.users("UUID") ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict pqktbRRtcMpnqyeZYlwb2mIstoXhQ3AYDx6BkiXc70Wfq8OSLKTDx0KKwdb0wUS

