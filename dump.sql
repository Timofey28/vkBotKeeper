--
-- PostgreSQL database dump
--

-- Dumped from database version 14.5
-- Dumped by pg_dump version 14.5


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

SET default_tablespace = '';

SET default_table_access_method = heap;


CREATE TABLE public.intermediate_information (
    subject_name character varying DEFAULT ''::character varying,
    user_id integer NOT NULL,
    date_of_lecture date DEFAULT NULL,
    material_id integer DEFAULT 0,
    materials_order bigint[]
);

ALTER TABLE public.intermediate_information OWNER TO postgres;


CREATE TABLE public.materials (
    id integer NOT NULL,
    user_id integer NOT NULL,
    subject_id integer NOT NULL,
    photo_link character varying,
    caption text,
    date_of_lecture date NOT NULL,
    adding_time timestamp without time zone NOT NULL,
    deletion_time timestamp without time zone
);

ALTER TABLE public.materials OWNER TO postgres;


CREATE SEQUENCE public.materials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE public.materials_id_seq OWNER TO postgres;
ALTER SEQUENCE public.materials_id_seq OWNED BY public.materials.id;


CREATE TABLE public.showing_orders (
    id integer NOT NULL,
    user_id integer NOT NULL,
    subject_id integer NOT NULL,
    date_of_lecture date NOT NULL,
    showing_order bigint[]
);

ALTER TABLE public.showing_orders OWNER TO postgres;


CREATE SEQUENCE public.showing_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE public.showing_orders_id_seq OWNER TO postgres;
ALTER SEQUENCE public.showing_orders_id_seq OWNED BY public.showing_orders.id;


CREATE TABLE public.subjects (
    id integer NOT NULL,
    name character varying NOT NULL,
    user_id integer NOT NULL
);

ALTER TABLE public.subjects OWNER TO postgres;


CREATE SEQUENCE public.subjects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE public.subjects_id_seq OWNER TO postgres;
ALTER SEQUENCE public.subjects_id_seq OWNED BY public.subjects.id;


CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    surname character varying(50),
    sex character varying(6) NOT NULL,
    profile_link character varying NOT NULL,
    vk_id integer NOT NULL,
    status character varying(50) NOT NULL,
    subject_user_is_in_rn integer DEFAULT 0,
    current_subject_name character varying DEFAULT ''::character varying,
    CONSTRAINT sex_constraint CHECK ((((sex)::text = 'male'::text) OR ((sex)::text = 'female'::text))),
    CONSTRAINT status_constraint CHECK ((((status)::text = 'main_menu'::text) OR ((status)::text = 'choose_subject'::text) OR ((status)::text = 'in_subject'::text) OR ((status)::text = 'show_materials'::text) OR ((status)::text = 'add_materials'::text) OR ((status)::text = 'add_subject'::text) OR ((status)::text = 'delete_subject'::text) OR ((status)::text = 'confirmation_delete_subject'::text) OR ((status)::text = 'choose_adding_day_from_list'::text) OR ((status)::text = 'add_to_specific_day'::text) OR ((status)::text = 'choose_showing_day_from_list'::text) OR ((status)::text = 'delete_materials'::text) OR ((status)::text = 'recover_materials'::text) OR ((status)::text = 'confirmation_delete_all_materials'::text) OR ((status)::text = 'choose_deleting_day_from_list'::text) OR ((status)::text = 'choose_materials_to_delete'::text) OR ((status)::text = 'choose_recovering_day_from_list'::text) OR ((status)::text = 'choose_materials_to_recover'::text) OR ((status)::text = 'edit_materials'::text) OR ((status)::text = 'choose_editing_day_from_list'::text) OR ((status)::text = 'choose_material_to_edit'::text) OR ((status)::text = 'edit_specific_material'::text) OR ((status)::text = 'add_to_specific_day_to_specific_place'::text)))
);

ALTER TABLE public.users OWNER TO postgres;


CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE public.users_id_seq OWNER TO postgres;
ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;

ALTER TABLE ONLY public.materials ALTER COLUMN id SET DEFAULT nextval('public.materials_id_seq'::regclass);
ALTER TABLE ONLY public.showing_orders ALTER COLUMN id SET DEFAULT nextval('public.showing_orders_id_seq'::regclass);
ALTER TABLE ONLY public.subjects ALTER COLUMN id SET DEFAULT nextval('public.subjects_id_seq'::regclass);
ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_pk PRIMARY KEY (id);

ALTER TABLE ONLY public.showing_orders
    ADD CONSTRAINT showing_orders_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_pk PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pk PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_vk_id_key UNIQUE (vk_id);

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_fk0 FOREIGN KEY (user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_fk1 FOREIGN KEY (subject_id) REFERENCES public.subjects(id);

