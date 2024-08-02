SET check_function_bodies = false;
CREATE FUNCTION public.set_current_timestamp_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  _new record;
BEGIN
  _new := NEW;
  _new."updated_at" = NOW();
  RETURN _new;
END;
$$;
CREATE TABLE public.anchors (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "column" text,
    dist_right integer,
    dist_down integer,
    radius integer,
    selector uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    anchor_text text
);
CREATE TABLE public.selectors (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    trigger_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE ONLY public.anchors
    ADD CONSTRAINT anchors_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.selectors
    ADD CONSTRAINT selectors_pkey PRIMARY KEY (id);
CREATE TRIGGER set_public_anchors_updated_at BEFORE UPDATE ON public.anchors FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();
COMMENT ON TRIGGER set_public_anchors_updated_at ON public.anchors IS 'trigger to set value of column "updated_at" to current timestamp on row update';
CREATE TRIGGER set_public_selectors_updated_at BEFORE UPDATE ON public.selectors FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();
COMMENT ON TRIGGER set_public_selectors_updated_at ON public.selectors IS 'trigger to set value of column "updated_at" to current timestamp on row update';
ALTER TABLE ONLY public.anchors
    ADD CONSTRAINT anchors_selector_fkey FOREIGN KEY (selector) REFERENCES public.selectors(id) ON UPDATE CASCADE ON DELETE CASCADE;
